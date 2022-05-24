import random

import mariadb
import sys
import numpy
import itertools

number_of_sensors = 2

def main():
    USER = "user1"  # michael's computer is: user1 password1.
    PASSWORD = "password1"  # 237 rpi is: root password1
    HOST = "127.0.0.1"
    PORT = 3306
    DATABASE = "projekts"
    AUTOCOMMIT = True

    number_of_entries = 300
    delete_old = True
    the_sensor_table = ["sensor"]

    sensors = []
    for index in range(1, number_of_sensors + 1):
        sensors.append("sensor" + str(index))

    number_of_actual_sensors_to_add = 0

    try:
        connection = mariadb.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            database=DATABASE,
            autocommit=AUTOCOMMIT
        )
        print("Flusher successfully connected to database '" + DATABASE + "'")

    except mariadb.Error as e:
        print("Flusher' has failed to connect to database '" + DATABASE + "'")
        print(f"{e}")
        sys.exit(1)

    cursor = connection.cursor()

    list_of_siners = []
    for index in range(number_of_sensors*3):
        list_of_siners.append(Sines())
    sines_cycler = itertools.cycle(list_of_siners)

    if delete_old:
        for sensor_name in the_sensor_table:
            answer = 0
            cursor.execute(
                f"SELECT EXISTS (SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_NAME = '{sensor_name}');")
            for mariadb_set in cursor:
                for data_field in mariadb_set:
                    answer = data_field
                    print("answer: " + str(answer))

            if answer == 1:  # 1 means there is already existing table, so drop it.
                cursor.execute(f"DROP TABLE {sensor_name};")
                print(f"dropped {sensor_name} table")
            else:  # 0 means there is no table (so dont drop table)
                print(f"no {sensor_name} table found, dont drop")
            cursor.execute(
                f"CREATE TABLE projekts.{sensor_name}(measure_id INT(11) NOT NULL AUTO_INCREMENT,sensor_name VARCHAR(10) DEFAULT NULL,temperature VARCHAR(10) DEFAULT NULL,humidity VARCHAR(10) DEFAULT NULL,light VARCHAR(10) DEFAULT NULL,message_on_off VARCHAR(10) DEFAULT NULL, mac VARCHAR(20) DEFAULT NULL, ts timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,PRIMARY KEY (measure_id));")
            print(f"created new {sensor_name} table")

    for sensor_name in the_sensor_table:
        number_of_actual_sensors_to_add += 1
        for index in range(number_of_entries):

            for sensor_n in sensors:
                mac = 'BE:FB:E4:4A:6A:10'
                if sensor_n == "sensor2":
                    mac = '00:00:00:00:00:01'

                cursor.execute(f"INSERT INTO projekts.{sensor_name}(sensor_name, temperature, humidity, light, message_on_off, mac) VALUES (" +
                               f"'{sensor_n}'" + "," +
                               str(next(sines_cycler).sines_numbers()) + "," +
                               str(next(sines_cycler).sines_numbers()) + "," +
                               str(next(sines_cycler).sines_numbers()) + "," +
                               "'on'" + "," +
                               f"'{mac}'" + ");")
        print(f"done filling in: {number_of_entries} number of {sensors} entries")

    total = number_of_entries * number_of_actual_sensors_to_add

    print(f"done filling {total} total amount of sensor entries")


def random_numbers(min, max):
    return random.randint(min, max)


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
            print("created new sines")
            print("ampl: " + str(self.sine_amp))
            print("sine_phase_length: " + str(self.sine_phase))
            print("sine_phase_cur: " + str(self.sine_x_cur))

        self.plot_y = self.sine_amp * .5 * (
            numpy.sin(((1 / self.sine_phase) * self.sine_x_cur - .5) * numpy.pi)) \
                      + .5 * self.sine_amp + self.old_plot_y
        self.plot_y = round(self.plot_y, 2)
        self.sine_x_cur += 1
        print("plot_y: " + str(self.plot_y))
        print("old_y:" + str(self.old_plot_y))
        return self.plot_y


main()
