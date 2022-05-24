import multiprocessing
import subprocess

import mariadbmanager
import grapher
import webserver
import sensormanager
import mqttmanager
import timemanager

server_ip = "10.120.0.211"
#server_ip = "127.0.0.1"


def main():
    print(subprocess.run(["kill_server"], shell=True))
    print(subprocess.run(["redis"], shell=False))
    
    webserver_queue = multiprocessing.Queue()

    mariadb_manager = mariadbmanager.MariaDBManager()
    plot_maker = grapher.Grapher()
    web_server = webserver.Webserver(server_ip, webserver_queue)
    sensor_manager = sensormanager.SensorManager(mariadb_manager, plot_maker)
    mqtt_manager = mqttmanager.MQTTManager(server_ip, sensor_manager)
    time_manager = timemanager.TimeManager(mqtt_manager, sensor_manager, webserver_queue)

    web_process = multiprocessing.Process(target=web_server.start_server)
    web_process.start()

    time_process = multiprocessing.Process(target=time_manager.loop_forever)
    time_process.start()


main()

