import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64
import datetime

import pandas as pd

import matplotlib
matplotlib.use('Agg')


class Grapher:
    def __init__(self):
        self.x_data = range(0, 288)

        self.db_field_name_to_title_name = {"temperature": "Temperature",
                                            "humidity": "Humidity",
                                            "light": "Light"}

        self.y_label_dict = {"Temperature": "Temperature (°C)",
                             "Humidity": "Humidity (milligrams per litre)",
                             "Light": "Light (lumens)"}

        self.img = BytesIO()

    def refresh_img(self):
        self.img = BytesIO()

    def create_plot(self, sensor, y_data_str):  # data_type is mariadb format name
        y_data = []
        for entry in y_data_str:
            y_data.insert(0, float(entry))

        self.refresh_img()
        #sensor_name = sensor.get_name()
        data_type = sensor.get_selected_data()
        date_length = 288

        # the following code is to make the plot look nicer
        data_name = self.db_field_name_to_title_name.get(data_type)

        y_data_length = len(y_data)

        if y_data_length < date_length:  # if there is no 288 entries in mariadb, add 0s to beginning
            for index_ in range(y_data_length, date_length):
                y_data.insert(0, 0)
        else:
            for index_ in range(y_data_length-date_length):
                #print("removed: " + str(y_data[0]))
                y_data.pop(0)

        # y-axis ytick font
        plt.yticks(np.arange(0.0, 105.0, 5.0))  # 105 - 5 = 100
        plt.yticks(fontsize=9)

        # x-axis xtick font. date_length = 300 = 24hr
        now_time = datetime.datetime.now().replace(microsecond=0, second=0)
        five_min_rounded_time = self.round_time(now_time, 5 * 60)
        times = pd.date_range(five_min_rounded_time, periods=288, freq='-5min')
        fig, ax = plt.subplots(1, 1)

        x_ticks = []
        for index in range(24):  # 24hrs
            hour_t = five_min_rounded_time - datetime.timedelta(hours=1 * index)
            ticker_string = ""
            if hour_t.hour == 0:
                ticker_string = str(hour_t.strftime("%y-%m-%d %H:%M"))
            elif index != 23:
                ticker_string = str(hour_t.strftime("%H:%M"))
            else:  # hour == 23
                ticker_string = str(hour_t.strftime("%y-%m-%d %H:%M"))
            #print(ticker_string)
            x_ticks.append(ticker_string)

        plt.plot(times, y_data)

        x_to_apply_tickers_to = []
        #print("start sorting % 12")
        for ind, ticker in enumerate(times):
            if ind % 12 == 0:
                x_to_apply_tickers_to.append(ticker)
                #print(ticker)
        x_to_apply_tickers_to.reverse()
        plt.gca().invert_xaxis()
        ax.set_xticks(x_to_apply_tickers_to)
        ax.set_xticklabels(x_ticks, rotation=50, fontsize=10)
        ax.tick_params(which="major", length=10)

        plt.setp(ax.xaxis.get_majorticklabels(), ha='right')

        # title and axis labels
        hours = "{:.0f}".format(date_length/12)
        ax.set_title(f"""Room {sensor.get_number()}'s {data_name} over {hours} hours""")
        ax.set_xlabel(f'{hours} hours of time (YY-MM-DD HH:MM)')

        y_label = self.y_label_dict.get(data_name)
        ax.set_ylabel(y_label)

        # remove excess border margin
        plt.tight_layout()

        # grid
        plt.grid()

        # save the current plot image
        plt.savefig(self.img, format='jpg', dpi=100)
        plt.close()

        # send it off
        return base64.b64encode(self.img.getvalue()).decode('utf8')

    @staticmethod
    def round_time(dt=None, round_to=60):
        """Round a datetime object to any time lapse in seconds
       dt : datetime.datetime object, default now.
       roundTo : Closest number of seconds to round to, default 1 minute.
       Author: Thierry Husson 2012 - Use it as you want but don't blame me.
       """
        if dt == None: dt = datetime.datetime.now()
        secs = (dt.replace(tzinfo=None) - dt.min).seconds
        rounding = (secs // round_to) * round_to
        return dt + datetime.timedelta(0, rounding - secs, -dt.microsecond)
