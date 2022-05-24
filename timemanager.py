import datetime
import enum


class State(enum.Enum):
    WAIT = 1
    WARNING = 2
    COLLECTING = 3


class TimeManager:
    def __init__(self, mqtt_manager, sensor_manager, webserver_queue):
        self.mqtt_manager = mqtt_manager
        self.sensor_manager = sensor_manager
        self.webserver_queue = webserver_queue

        self.warning_time = datetime.datetime.now()  # five minute interval 30s before 5min rounding i.e. 14:34:30
        self.master_time = datetime.datetime.now()  # time when data is expected to be received. 5s before 5 min rounding i.e. 14:34:55
        self.reset_time = datetime.datetime.now()

        self.state = State.WAIT

    def loop_forever(self):
        print("TimeManager: entered loop_forever.")
        self.set_times()
        # tell webserver how many sensors there currently are
        self.webserver_queue.put(len(self.sensor_manager.sensors))

        while not self.webserver_queue.empty():
            pass
        print("TimeManager: queue is now empty")

        while True:
            now_time = datetime.datetime.now()
            if self.state == State.WAIT:
                if self.warning_time < now_time:
                    print("TimeManager: WAIT OVER. PUBLISH WARNING.")
                    self.state = State.WARNING
                    self.mqtt_manager.reconnect()
                    self.mqtt_manager.publish_warning("WARNING")
                else:
                    self.check_queue()  # check button pushed from client-side
            elif self.state == State.WARNING:
                if self.master_time < now_time:
                    print("TimeManager: MASTER TIME NOW. START COLLECTING.")
                    self.state = State.COLLECTING
            elif self.state == State.COLLECTING:
                if self.reset_time < now_time:
                    print("TimeManager: COLLECTING OVER. RESET.")
                    self.state = State.WAIT
                    self.set_times()
                    # make sensor_manager update the webserver
                    self.sensor_manager.five_minute_update()
                else:
                    self.mqtt_manager.loop_short()
                    # check button push
                    self.check_queue()

    def check_queue(self):
        while not self.webserver_queue.empty():
            #print(str(self.webserver_queue.get()))
            get = self.webserver_queue.get()
            self.sensor_manager.change_sensor_select_data(get[0], get[1])
            self.sensor_manager.update_graph(get[0])

    def set_times(self, multiplier=1):
        print("now_time: " + str(datetime.datetime.now()))
        self.warning_time = self.round_time(300, 295)  # 4:55 (300, 295). 5, 5
        print("warning_time: " + str(self.warning_time))
        self.master_time = self.warning_time + datetime.timedelta(0, 0)  # 4:55. admittedly this is not really used.
        print("master_time: " + str(self.master_time))
        self.reset_time = self.master_time + datetime.timedelta(0, 15)  # 5:10 (0, 15). (0, 5)
        print("reset_time: " + str(self.reset_time))

    @staticmethod
    def round_time(round_to, addition):
        """Round a datetime object to any time lapse in seconds
        dt : datetime.datetime object, default now.
        roundTo : Closest number of seconds to round to, default 1 minute.
        Author: Thierry Husson 2012 - Use it as you want but don't blame me.
        """
        dt = datetime.datetime.now()
        secs = (dt.replace(tzinfo=None) - dt.min).seconds
        rounding = ((secs) // round_to) * round_to  # round to closest  + round_to/2. round down.
        return dt + datetime.timedelta(0, rounding - secs + addition, -dt.microsecond)
