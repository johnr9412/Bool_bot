import json


class StageSchedule:
    stage_name = ''
    artists = list()

    def __init__(self, stage_name, artist):
        self.stage_name = stage_name
        self.artists = list()
        self.artists.append(artist)


class Schedule:
    day = ''
    stage_schedules = {}

    def __init__(self):
        self.day = ''
        self.stage_schedules = {}

    def __init__(self, day):
        self.day = day
        self.stage_schedules = {}

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=False)

    def add_artist(self, stage_name, artist):
        if self.stage_schedules.get(stage_name) is None:
            self.stage_schedules[stage_name] = StageSchedule(stage_name, artist)
        else:
            self.stage_schedules[stage_name].artists.append(artist)
