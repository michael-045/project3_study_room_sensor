import paho.mqtt.client as mqtt
import enum
import sys

class CollectState(enum.Enum):
    NOCOLLECTING = 1
    COLLECTING = 2

class MQTTManager:
    def __init__(self, server_ip, sensor_manager):
        self.server_ip = server_ip
        self.sensor_manager = sensor_manager
        self.client = mqtt.Client()
        self.collect_state = CollectState.NOCOLLECTING
        self.checksum = 0
        self.insert_data = []
        self.data_row = [None]*6
        self.current_sensor = ""

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.tls_set(ca_certs="mqtt/ca.crt",
                            certfile="mqtt/server.crt",
                            keyfile="mqtt/server.key")
        self.client.tls_insecure_set(True)
        self.client.connect(server_ip, 8883, 60)  # 8883

        self.client.publish("test", "test1")

    def reconnect(self):
        self.client.connect(self.server_ip, 8883, 60)  # 8883

    def on_connect(self, client, userdata, flags, rc):
        print("MQTTManager connected to MQTT with result code " + str(rc))
        client.subscribe('sensors/#')
        client.subscribe('collect')
        client.subscribe('collect/#')

    def on_message(self, client, userdata, msg):
        print("MQTTManager, on_message: " + msg.topic + " " + str(msg.payload))
        if self.collect_state == CollectState.COLLECTING:
            if not "collect" in msg.topic:
                # check if checksum matches
                if self.checksum == len(self.insert_data):
                    # correct, now insert
                    print("CollectState: Matched!")
                    print(f"CollectState: checksum: {self.checksum}")
                    self.collect_state = CollectState.NOCOLLECTING
                    self.sensor_manager.insert_replace_mariadb(self.insert_data)
                    self.insert_data = []
                else:
                    print("CollectState: DID NOT MATCH!")
                    print(f"CollectState: checksum: {self.checksum}")
                    print(f"CollectState: insert_data: {len(self.insert_data)}")
                    sys.exit(0)
            else:  # collect the data into a data_row and insert it into insert_data.
                is_it_ready = True
                payload = msg.payload.decode('utf-8')
                print("CollectState: get the data, send into insert_data")
                self.current_sensor = msg.topic[8:15]
                if f"collect/{self.current_sensor}/temperature" in msg.topic:
                    self.data_row[1] = payload
                elif f"collect/{self.current_sensor}/humidity" in msg.topic:
                    self.data_row[2] = payload
                elif f"collect/{self.current_sensor}/light" in msg.topic:
                    self.data_row[3] = payload

                for index in range(1, 4):  # 1, 2, 3
                    if self.data_row[index] is None:
                        is_it_ready = False

                if is_it_ready:
                    self.data_row[0] = self.current_sensor
                    self.data_row[4] = "off"
                    self.insert_data.append(self.data_row)
                    self.data_row = [None] * 6

        else:  # check if got collect
            if msg.topic == "collect":
                self.checksum = int(msg.payload.decode('utf-8'))
                self.collect_state = CollectState.COLLECTING
                print(f"CollectState: checksum is: {self.checksum}")
            else:  # continue as normal
                self.sensor_manager.data_mqtt_to_mariadb(msg.topic, msg.payload)

    def loop_short(self):
        self.client.loop(.2)

    def publish_warning(self, millis):
        print("publish warning")
        self.client.publish("warning", millis)
        #print("MQTTManager published warning.")
