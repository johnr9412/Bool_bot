import boto3
import requests
import dateutil.tz
import os
import json
from datetime import datetime
from warrant.aws_srp import AWSSRP


dynamodb = boto3.resource('dynamodb', region_name="us-east-2")
USERNAMES = dynamodb.Table('stridekick_crosswalk').scan()['Items']


def get_users_name(username):
    try:
        user = next(filter(lambda x: x['stridekick_name'] == username, USERNAMES))
        return user['person_name']
    except Exception as e:
        print(e)
        return username


def warrant_auth(username, password):
    pool_id = os.environ['POOL_ID']
    client_id = os.environ['CLIENT_ID']
    aws = AWSSRP(username=username, password=password, pool_id=pool_id,
                 client_id=client_id, pool_region='us-east-1')
    tokens = aws.authenticate_user()
    access_token = tokens['AuthenticationResult']['AccessToken']
    return access_token


def format_step_data(step_data):
    step_metrics = {}
    for person in step_data:
        step_metrics[get_users_name(person['username'])] = person['activity']['steps']
    return {k: v for k, v in sorted(step_metrics.items(), key=lambda item: item[1], reverse=True)}


def get_step_data(token):
    url = 'https://app.stridekickapp.com/graphql'
    data = {
        "operationName": "Friends",
        "query": "query Friends($date: String, $search: String) {\n  me {\n    id\n    avatar\n    unitType\n    username\n    activity(date: $date) {\n      id\n      distance\n      minutes\n      steps\n      __typename\n    }\n    friends(search: $search) {\n      hits\n      members {\n        id\n        avatar\n        firstName\n        lastName\n        username\n        activity(date: $date) {\n          id\n          distance\n          minutes\n          steps\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    memberFriends {\n      id\n      __typename\n    }\n    __typename\n  }\n}",
        "variables":
            {
                "date": datetime.now(tz=dateutil.tz.gettz('US/Eastern')).strftime('%Y-%m-%d'),
                "search": ""
            }
    }

    headers = {
        'authorization': "Bearer " + token,
        'Apollo-Require-Preflight': 'true',
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=data, headers=headers)
    step_data = json.loads(response.content)['data']['me']['friends']['members']
    return format_step_data(step_data)


def scrape_fitness_metrics(usrnm, pswd):
    token = warrant_auth(usrnm, pswd)
    return get_step_data(token)


def create_step_embed(steps_dict):
    embed_fields = [{
        "name": "Date",
        "value": datetime.now(tz=dateutil.tz.gettz('US/Eastern')).strftime('%m-%d-%Y'),
        "inline": False
    }]

    message_text = ''
    for item in steps_dict:
        if steps_dict[item] != 0:
            message_text += (item + ': ' + "{:,}".format(steps_dict[item]) + '\n')
    embed_fields.append({
        "name": "Step Counts",
        "value": message_text,
        "inline": False
    })

    embed_fields.append({
        "name": "Reminder",
        "value": "Sync your steps or the devil will get you",
        "inline": False
    })

    embed = {
        "title": "Steps",
        "color": 3447003,
        "fields": embed_fields
    }
    return embed


def update_discord_message(app_id, token, step_embed):
    url = "https://discord.com/api/v10/webhooks/" + str(app_id) + "/" + token + "/messages/@original"
    data = {
        "embeds": [step_embed]
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


def lambda_handler(event, context=None):
    step_embed = create_step_embed(scrape_fitness_metrics(event['username'], event['password']))
    update_discord_message(event['app_id'], event['token'], step_embed)
    try:
        return {
            'statusCode': 200,
            'body': "Success"
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500
        }
