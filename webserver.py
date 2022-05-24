from flask import Flask, render_template, json
from flask_socketio import SocketIO, emit

import eventlet
eventlet.monkey_patch()

buttonDict = {"tempBtn": "temperature",
              "humiBtn": "humidity",
              "lighBtn": "light"}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", message_queue='redis://', async_mode='eventlet')

sensor_num = 0
queue = None


class Webserver:
    def __init__(self, server_ip, webserver_queue):
        global queue
        self.server_ip = server_ip
        self.webserver_queue = webserver_queue
        queue = webserver_queue

    # server start methods
    def start_server(self):
        global sensor_num
        while queue.empty():
            pass
        if not queue.empty():
            sensor_num = queue.get()
            print("QUEUE GET " + str(sensor_num))
        socketio.run(app, host=self.server_ip)  # rpi ip: 10.120.0.211

        print("only land here when server is exited")

    @staticmethod
    @app.route('/')
    def index():
        return render_template('index.html', async_mode=socketio.async_mode)

    @staticmethod
    @socketio.event
    def build_multi():  # builds the number of sensor interfaces
        socketio.emit('js_build_multi', {"total_sensors": sensor_num})

    @staticmethod
    @socketio.event
    def button_pressed(classes):  # called from javascript

        # 0: graphButtonClass 1: s1 2: tempBtn
        split_classes = classes.split(" ")
        data_type = buttonDict.get(split_classes[2])
        sensor_number = int(split_classes[1][1:2])
        queue.put((sensor_number, data_type))

    @staticmethod
    @socketio.event
    def my_ping():  # called from javascript
        # print("my_ping received")
        emit('my_pong')

    @staticmethod
    @socketio.event
    def connect():  # when a client connects, do this.
        print("Webserver: Someone Connected.")
        Webserver.build_multi()
        # maybe should update graph and table on connection here
