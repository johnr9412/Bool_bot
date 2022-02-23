from methods import get_schedule
from urllib.parse import urlparse
from urllib.parse import parse_qs


def lambda_handler(event, context):
    return_messages = []
    try:
        url_string = event['schedule_url']
        if '/m/' in url_string:
            event_name = url_string.split('/m/')[1].split('/?')[0]
        else:
            event_name = url_string.split('/s/')[1].split('/?')[0]
        parsed_url = urlparse(url_string)
        cf_user = ''
        if 'user' in url_string:
            cf_user = parse_qs(parsed_url.query)['user'][0]
        return_messages.extend(get_schedule.get_event_schedule_for_user(event_name, cf_user))
    except Exception as e:
        print(e)
        return_messages.append("An error occured")
    return return_messages
