import json
import time
import boto3
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


def lambda_handler(event, context):
    http_method = event['httpMethod']
    if http_method == 'GET':
        event_name = event['queryStringParameters']['event_name']
        return_string = get_countdown(event_name)
    elif http_method == 'POST':
        body = json.loads(event['body'])
        if write_event(body['event_name'], body['event_date']):
            return_string = 'Added'
        else:
            return_string = 'Borked'
    else:
        return_string = 'herp'
    return {
        'statusCode': 200,
        'body': return_string
    }
