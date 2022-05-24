import mariadb
import sys

USER = "user1"  # michael's computer is: user1 password1.
PASSWORD = "password1"  # 237 rpi is: root password1
HOST = "127.0.0.1"
PORT = 3306
DATABASE = "projekts"
AUTOCOMMIT = True


class MariaDBManager:
    def __init__(self):
        try:
            self.connection = mariadb.connect(
                user=USER,
                password=PASSWORD,
                host=HOST,
                port=PORT,
                database=DATABASE,
                autocommit=AUTOCOMMIT
            )
            print("MariaDBManager has successfully connected to database '" + DATABASE + "'")

        except mariadb.Error as e:
            print("MariaDBManager has failed to connect to database '" + DATABASE + "'")
            print(f"{e}")
            sys.exit(1)

        self.cursor = self.connection.cursor()
        self.row_set = [None]*6

    def exc_query(self, query, *args):
        data = []
        self.cursor.execute(query.format(*args))
        #print("cur: ")
        #print(self.cursor)
        for isitaset in self.cursor:
            #print("isitaset: ")
            #print(isitaset)
            for data_field in isitaset:
                #print("inside datafields: " + str(data_field))
                data.append(data_field)
        return data

    def exc_insert(self, insert, *args):
        formatted = insert.format(*args)
        #print(str(formatted))
        self.cursor.execute(formatted)

    def insert_replace(self, sensor_name, insertion_data):
        print("insertion data: " + str(insertion_data))
        checksum = len(insertion_data)
        print(f"checksum: {checksum}")
        # get measure_ids
        measure_ids = self.exc_query(f"SELECT measure_id FROM sensor WHERE (sensor_name, message_on_off) = ('{sensor_name}', 'off') ORDER BY measure_id DESC LIMIT {checksum};")
        # delete
        self.cursor.execute(f"DELETE FROM sensor WHERE (sensor_name, message_on_off) = ('{sensor_name}', 'off') ORDER BY measure_id DESC LIMIT {checksum};")
        # insert
        for index in range(checksum):
            self.cursor.execute(f"INSERT INTO sensor (measure_id, sensor_name, temperature, humidity, light, message_on_off, mac) VALUES "
                                f"({measure_ids[index]}, '{sensor_name}', {insertion_data[index][1]}, {insertion_data[index][2]}, {insertion_data[index][3]}, 'was off', 'was off');")
        print("inserted done")

    def data_mqtt_to_mariadb(self, topic, payload):
        if len(topic) < 16:
            return

        payload = payload.decode('utf-8')
                                   #  0123456789012345
        sensor_name = topic[8:15]  # "collect/sensor1/temperature"[8:15]
        sensor_number = int(topic[14:15])
        all_rows = True

        if f"sensors/{sensor_name}/name" in topic:
            self.row_set[0] = sensor_name
        elif f"sensors/{sensor_name}/temperature" in topic:
            self.row_set[1] = payload
        elif f"sensors/{sensor_name}/humidity" in topic:
            self.row_set[2] = payload
        elif f"sensors/{sensor_name}/light" in topic:
            self.row_set[3] = payload
        elif f"sensors/{sensor_name}/on_off" in topic:
            self.row_set[4] = payload
        elif f"sensors/{sensor_name}/mac" in topic:
            self.row_set[5] = payload

        print(self.row_set)

        for value in self.row_set:
            if value is None:
                all_rows = False

        if all_rows is True:
            print("now execute mariadb")
            self.cursor.execute(f"INSERT INTO projekts.sensor(sensor_name, temperature, humidity, light, message_on_off, mac ) VALUES (" +
                f"'{sensor_name}'" + "," +
                str(self.row_set[1]) + "," +
                str(self.row_set[2]) + "," +
                str(self.row_set[3]) + "," +
                f"'{self.row_set[4]}'" + "," +
                f"'{self.row_set[5]}'" + ");")
            self.row_set = [None]*6
            return (True, sensor_number)
        else:
            return (False, sensor_number)
