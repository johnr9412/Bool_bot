import json
import time
import boto3
import os
import requests
from datetime import datetime
from boto3.dynamodb.conditions import Key

COUNTDOWN_TABLE = boto3.resource('dynamodb').Table('event_countdowns')


def get_days_difference(event_date):
    currentDateWithoutTime = datetime.now().date()
    if event_date > currentDateWithoutTime:
        delta = event_date - currentDateWithoutTime
        return delta.days
    else:
        return 0


def get_countdown(event_name):
    try:
        resp = COUNTDOWN_TABLE.query(KeyConditionExpression=Key('event_name').eq(event_name))
        event = resp.get('Items')[0]
        event_date = datetime.strptime(event['event_date'], '%Y-%m-%d %H:%M:%S').date()
        days_diff = get_days_difference(event_date)
        return_str = ('{} day until ' + event_name) if days_diff == 1 else ('{} days until ' + event_name)
        return return_str.format(days_diff)
    except Exception as e:
        print(e)
        return 'Something went wrong'


def write_event(event_name, str_event_date):
    try:
        event_date = datetime.strptime(str_event_date, '%Y-%m-%d')
        with COUNTDOWN_TABLE.batch_writer() as writer:
            writer.put_item(
                Item={'event_name': event_name, 'date_added': str(time.time()), 'event_date': str(event_date)}
            )
        return True
    except Exception as e:
        print(e)
        return False


def update_discord_message(app_id, token, return_string):
    url = "https://discord.com/api/v10/webhooks/" + str(app_id) + "/" + token + "/messages/@original"
    data = {
        "content": return_string
    }
    if str(app_id) == '1241478241269579836':
        headers = {
            "Authorization": "Bot " + os.environ['TEST_BOT_TOKEN']
        }
    else:
        headers = {
            "Authorization": "Bot " + os.environ['BOOL_BOT_TOKEN']
        }
    r = requests.patch(url, headers=headers, json=data)
    print(r.status_code)


def lambda_handler(event, context):
    event_name = event['event_name']
    app_id = event['app_id']
    token = event['token']
    return_string = get_countdown(event_name)
    update_discord_message(app_id, token, return_string)
    return {
        'statusCode': 200,
        'body': return_string
    }
