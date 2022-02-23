import json


class StageSchedule:
    stage_name = ''
    shows = list()

    def __init__(self, stage_name, artist):
        self.stage_name = stage_name
        self.shows = list()
        self.shows.append(artist)


class Schedule:
    day = ''
    stage_schedules = {}

    def __init__(self, day):
        self.day = day
        self.stage_schedules = {}

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=False)

    def add_show(self, stage_name, show):
        if self.stage_schedules.get(stage_name) is None:
            self.stage_schedules[stage_name] = StageSchedule(stage_name, show)
        else:
            self.stage_schedules[stage_name].shows.append(show)
