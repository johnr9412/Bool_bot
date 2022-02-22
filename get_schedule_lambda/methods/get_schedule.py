import requests
import pandas as pd
from dateutil import rrule
from datetime import datetime, timedelta
from methods.schedule_obj import Schedule, StageSchedule


def get_json(url):
    resp = requests.get(url=url)
    data = resp.json()
    return data['locations']


def get_schedule_ids(json_object):
    list_of_ids = []
    for stage in json_object:
        for show in stage['events']:
            list_of_ids.append(show['short'])

    return list_of_ids


def add_days_to_schedule(df):
    day = 1
    initial_time = df['start'].min().to_pydatetime().replace(hour=8, minute=00)
    max_time = df['start'].max().to_pydatetime()
    if int(max_time.strftime("%I")) > 8:
        max_time += timedelta(days=1)
    max_time.replace(hour=8, minute=00)
    for dt in rrule.rrule(rrule.DAILY,
                          dtstart=initial_time,
                          until=max_time):
        day_end = dt + timedelta(days=1)
        df.loc[
            (df['start'] >= dt) & (df['start'] <= day_end)
            , 'day'] = day
        day += 1
    return df


def create_event_schedule_df(event_url, schedule_ids):
    json_object = get_json(event_url)
    list_of_objects = []
    stage_count = 0
    for stage in json_object:
        stage_count += 1
        stage_name = stage['name']
        for show in stage['events']:
            short = show['short']
            list_of_objects.append(
                {
                    'short_id': short,
                    'artist': show['name'],
                    'start': datetime.strptime(show['start'], '%Y-%m-%d %H:%M'),
                    'end': datetime.strptime(show['end'], '%Y-%m-%d %H:%M'),
                    'day': 0,
                    'stage': stage_name,
                    'stage_priority': stage_count,
                    'attending': 1 if short in schedule_ids else 0
                })
    return pd.DataFrame.from_records([item for item in list_of_objects])\
        .sort_values(['start', 'stage_priority'], ascending=[True, True])


def make_artist_string(is_first_row, hour_start, hour_end, attending, artist):
    if is_first_row:
        artist_string = hour_start.strftime("%I") + '-' \
                        + (hour_end + timedelta(minutes=60)).strftime("%I%p")
    else:
        artist_string = '\t'
    artist_string += ' '
    if attending:
        artist_string += '**' + artist + '**'
    else:
        artist_string += artist

    return artist_string


def generate_string_list(sched_df):
    return_list = []
    first_set_datetime = sched_df['start'].min().to_pydatetime()
    last_set_datetime = sched_df['start'].max().to_pydatetime()
    for day in sched_df['day'].unique():
        shows_for_day = sched_df.loc[sched_df['day'] == day]
        day_string = shows_for_day['start'].min().to_pydatetime().strftime("%A")
        list_of_stages = shows_for_day.sort_values(['stage_priority'], ascending=[True])['stage'] \
            .unique().tolist()
        line_limit = 2000 / (len(list_of_stages) if len(list_of_stages) > 0 else 1)  # how many hours you can do
        counter = 0
        schedule_obj = Schedule(day_string)
        for hour_start in rrule.rrule(rrule.HOURLY, dtstart=first_set_datetime, until=last_set_datetime):
            hour_end = hour_start + timedelta(minutes=59)
            shows_for_hour = shows_for_day.loc[(shows_for_day['start'] >= hour_start)
                                               & (shows_for_day['start'] <= hour_end)]
            if len(shows_for_hour) > 0:
                for stage in list_of_stages:
                    artists_for_stage = shows_for_hour.loc[(shows_for_hour['stage'] == stage)]
                    if len(artists_for_stage) > 0:
                        time_count = 0
                        for index, row in artists_for_stage.iterrows():
                            artist_string = make_artist_string(time_count == 0, hour_start, hour_end,
                                                               int(row['attending']) == 1, row['artist'])
                            time_count += 1
                            schedule_obj.add_artist(stage, artist_string)
                            counter += 1
                    else:
                        artist_string = make_artist_string(True, hour_start, hour_end, False, '\t')
                        schedule_obj.add_artist(stage, artist_string)
                        counter += 0.25

                if counter >= line_limit:
                    return_list.append(schedule_obj.toJSON())
                    schedule_obj = Schedule(day_string)
                    counter = 0
        return_list.append(schedule_obj.toJSON())
    return return_list


def get_event_schedule_for_user(event_name, user):
    event_url = 'https://clashfinder.com/data/event/' + event_name + '.json'
    schedule_ids = []
    if user != '':
        schedule_url = event_url + '?user=' + user
        schedule_ids = get_schedule_ids(get_json(schedule_url))
    event_schedule_df = create_event_schedule_df(event_url, schedule_ids)
    event_schedule_df = add_days_to_schedule(event_schedule_df)
    return generate_string_list(event_schedule_df)
