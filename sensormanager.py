import sensorobject
import flask_socketio

ext_io = flask_socketio.SocketIO(message_queue='redis://')


class SensorManager:
    def __init__(self, mariadb_manager, grapher):
        self.sensors = []  # get number of sensors using len(sensors)
        self.mac_to_room = {"BE:FB:E4:4A:6A:10": "room1",
                            "00:00:00:00:00:01": "room2"}  # could implement feature to store this in a db table

        self.mariadb_manager = mariadb_manager
        self.grapher = grapher

        self.check_database_count()
        self.check_sensor_room()

    def change_sensor_select_data(self, sensor_number, data_type):
        sensor = self.sensors[sensor_number - 1]
        sensor.set_selected_data(data_type)

    def get_number_of_sensors(self):
        return len(self.sensors)

    def check_sensor_room(self):
        for sensor in self.sensors:
            last_mac = self.mariadb_manager.exc_query(
                f"SELECT mac FROM sensor WHERE sensor_name='{sensor.get_name()}' ORDER BY measure_id DESC LIMIT 1;")[0]
            last_room = self.mac_to_room.get(last_mac)
            sensor.set_room(last_room)

    def check_database_count(self):
        already_count = \
        self.mariadb_manager.exc_query("SELECT COUNT( DISTINCT sensor_name) as sensor_num from sensor;")[0]
        for index in range(len(self.sensors) + 1, already_count + 1):  # creates new sensor objects from already existing database
            self.create_new_sensor_object(f"sensor{index}")
            print(f"SensorManager created sensor{index}.")

    def create_new_sensor_object(self, name):
        self.sensors.append(sensorobject.SensorObject(name))  # composition

    def query_this_data_type(self, sensor_name, data_type):
        return self.mariadb_manager.exc_query(f"SELECT {data_type} FROM sensor WHERE sensor_name='{sensor_name}';")

    def insert_replace_mariadb(self, insert_data):
        sensor_name = insert_data[0][0]
        self.mariadb_manager.insert_replace(sensor_name, insert_data)

    def data_mqtt_to_mariadb(self, topic, payload):
        confirm_set = self.mariadb_manager.data_mqtt_to_mariadb(topic, payload)
        #print(f"confirm set: {confirm_set}")
        if confirm_set[0]:
            self.check_database_count()
            #print("inside confirm set")
            # true, then make that sensor object true
            self.sensors[confirm_set[1] - 1].set_updated_bool(True)  # confirms that this sensor was updated
            #print("get_updated_bool: " + str(self.sensors[confirm_set[1] -1].get_updated_bool()))
        else:
            pass #nothing

    def five_minute_update(self):
        print("FIVE MINUTE UPDATE")
        for sensor in self.sensors:
            #print("FIVEMIN get_updated_bool: " + str(sensor.get_updated_bool()))
            if sensor.get_updated_bool():
                print(sensor.get_name() + " was updated, now query and update :)")
                # True, means was updated. get the newest data added and send to webserver
                new_row = self.mariadb_manager.exc_query(
                    f"SELECT * FROM sensor WHERE sensor_name='{sensor.get_name()}' ORDER BY measure_id DESC LIMIT 1;")
                # send to webserver function. self.web_server.update_table(sensor, new_row)
                ext_io.emit('table_update', {'sensor_name': sensor.get_name(), 'sensor_num': sensor.get_number(),
                                                  'id': new_row[0], 'temp': new_row[2],
                                                  'humi': new_row[3], 'ligh': new_row[4],
                                                  'onoff': new_row[5], "mac": new_row[6],
                                                  'time': str(new_row[7])})
                # update graph
                self.update_graph(sensor.get_number())
            else:
                print(sensor.get_name() + " was not updated, now make extra duplicate.")
                # false, means did not catch the mqtt for this sensor.
                # create a duplicate of last measurement, and insert into.
                last_row = self.mariadb_manager.exc_query(
                    f"SELECT * FROM sensor WHERE sensor_name='{sensor.get_name()}' ORDER BY measure_id DESC LIMIT 1;")
                self.mariadb_manager.exc_insert(
                    f"INSERT INTO projekts.sensor(sensor_name, temperature, humidity, light, message_on_off, mac ) VALUES (" +
                    f"""'{last_row[1]}'""" + "," +
                    str(last_row[2]) + "," +
                    str(last_row[3]) + "," +
                    str(last_row[4]) + "," +
                    f"'off'" + "," +
                    f"'{last_row[6]}'" + ");")

                self.update_graph(sensor.get_number())
            sensor.set_updated_bool(False)

    def update_graph(self, sensor_number):
        print(f"1UPDATE GRAPH for sensor{sensor_number}")
        sensor = self.sensors[sensor_number - 1]
        # get y_data, create graph, send graph to webserver
        y_data = self.mariadb_manager.exc_query(
            f"SELECT {sensor.get_selected_data()} FROM sensor WHERE sensor_name='{sensor.get_name()}' ORDER BY measure_id DESC LIMIT 288;")
        base64_image = self.grapher.create_plot(sensor, y_data)
        ext_io.emit('graph_update', {'image': base64_image, 'sensor_num': sensor.get_number()})
