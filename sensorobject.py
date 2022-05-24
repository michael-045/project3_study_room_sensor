class SensorObject:
    def __init__(self, name):
        self.name = name
        self.selected_data = "temperature"
        self.number = int(name[6:7])
        self.room = ""

        self.updated_bool = False

    def get_name(self):
        return self.name

    def get_selected_data(self):
        return self.selected_data

    def set_selected_data(self, data_type):
        self.selected_data = data_type

    def get_number(self):
        return self.number

    def get_room(self):
        return self.room

    def set_room(self, room):
        self.room = room

    def get_updated_bool(self):
        return self.updated_bool

    def set_updated_bool(self, booleany):
        self.updated_bool = booleany

