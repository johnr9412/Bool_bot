import json
from methods import get_schedule
from urllib.parse import urlparse
from urllib.parse import parse_qs


def create_response(status_code, body):
    response = {
        "statusCode": status_code,
        "body": json.dumps(body)
    }
    return response


def lambda_handler(event, context):
    try:
        return_messages = []
        url_string = json.loads(event['body'])['schedule_url']
        if '/m/' in url_string:
            event_name = url_string.split('/m/')[1].split('/?')[0]
        else:
            event_name = url_string.split('/s/')[1].split('/?')[0]
        parsed_url = urlparse(url_string)
        cf_user = ''
        if 'user' in url_string:
            cf_user = parse_qs(parsed_url.query)['user'][0]
        return_messages.extend(get_schedule.get_event_schedule_for_user(event_name, cf_user))
        return create_response(200, return_messages)
    except Exception as e:
        print(e)
        return create_response(500, 'something went wrong in the lambda')
