import paho.mqtt.client as mqtt
import random
import time
import sys
import numpy
import itertools


class MQTTESP:
    def __init__(self, server_ip, data_generation):
        self.plot_y = 1

        self.old_plot_y = 0
        self.sine_amp = 1
        self.sine_phase = 1
        self.sine_x_cur = 1

        self.data_generation = data_generation

        self.server_ip = server_ip
        self.port = 1883

        # generate client ID with pub prefix randomly
        self.client_id = f'python-mqtt-{random.randint(0, 1000)}'

        self.topics = ["name", "temperature", "humidity", "light", "on_off", "mac"]

        self.pretopics = ["sensors/sensor1/",
                          "sensors/sensor2/"]
        self.sensor_to_room_dict = {"sensors/sensor1/": "BE:FB:E4:4A:6A:10",
                                    "sensors/sensor2/": "00:00:00:00:00:01"}
        list_of_siners = []
        for index in range(len(self.pretopics)):
            list_of_siners.append(Sines())
        self.siners = itertools.cycle(list_of_siners)

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(server_ip, 1883, 60)

        self.stuck_in_loop = True
        self.what_did_we_catch = 0

    def on_message(self, client, userdata, msg):
        print("on_message: " + msg.topic + " " + str(msg.payload))
        self.stuck_in_loop = False
        self.what_did_we_catch = int(msg.payload)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
            client.subscribe('warning')
        else:
            print("Failed to connect, return code %d\n", rc)

    def foreversuperloop(self):
        while True:
            # deep sleep for 8 sec
            time.sleep(9)

            # wake up then catch the warning
            while self.stuck_in_loop:
                self.client.loop()

            # once caught wait that amount of time
            print("sleep now")
            time.sleep(int(self.what_did_we_catch//1000))
            print("out of sleep")

            # time up now send data

            for pretopic in self.pretopics:
                time.sleep(0.2)
                for topic in self.topics:
                    time.sleep(0.1)
                    msg = str(self.plot_y)  # need to change this later
                    if topic == "name":
                        self.client.publish(pretopic + topic, pretopic[8:15])
                        print(f"{pretopic} + {topic}: {pretopic[8:15]}")
                        continue
                    elif topic == "on_off":
                        self.client.publish(pretopic + topic, "on")
                        print(f"{pretopic} + {topic}: on")
                        continue
                    elif topic == "mac":
                        self.client.publish(pretopic + topic, self.sensor_to_room_dict.get(pretopic))
                        print(f"{pretopic} + {topic}: {self.sensor_to_room_dict.get(pretopic)}")
                        continue
                    self.client.publish(pretopic + topic, msg)
                    print(f"{pretopic} + {topic}: {msg}")
                    self.plot_y = next(self.siners).sines_numbers()

            # now should have sent completely
            print("done publishing. looping again")
            self.stuck_in_loop = True
            self.what_did_we_catch = 0


class Sines:
    def __init__(self):
        self.plot_y = 1

        self.old_plot_y = 0
        self.sine_amp = 1
        self.sine_phase = 1
        self.sine_x_cur = 1

    def sines_numbers(self):
        if self.sine_phase == self.sine_x_cur:  # will activate on first go
            self.old_plot_y = self.plot_y
            self.sine_x_cur = 0
            self.sine_phase = random.randint(40,
                                             120)  # generate the sine_x a random length then divide by 3 because of the 3 different fields.
            self.sine_amp = random.randint(20, 40)
            if self.plot_y > 70:  # not strictly bound to 20-80
                # should decrease
                self.sine_amp = -self.sine_amp
            elif self.plot_y < 30:
                # should increase
                pass
            elif random.randint(1, 2) == 1:
                self.sine_amp = -self.sine_amp  # lost the coin flip, so should be negative
            else:
                pass  # won the coin flip, so stay positive
            #print("created new sines")
            #print("ampl: " + str(self.sine_amp))
            #print("sine_phase_length: " + str(self.sine_phase))
            #print("sine_phase_cur: " + str(self.sine_x_cur))

        self.plot_y = self.sine_amp * .5 * (
            numpy.sin(((1 / self.sine_phase) * self.sine_x_cur - .5) * numpy.pi)) \
                      + .5 * self.sine_amp + self.old_plot_y
        self.plot_y = round(self.plot_y, 2)
        self.sine_x_cur += 1
        #print("plot_y: " + str(self.plot_y))
        #print("old_y:" + str(self.old_plot_y))
        return self.plot_y


mqttesp = MQTTESP("10.42.0.2", "sines")  # "10.120.0.237"
mqttesp.foreversuperloop()