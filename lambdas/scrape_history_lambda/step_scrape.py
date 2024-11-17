import json
import requests
import os
import dateutil.tz
from datetime import datetime, timedelta
from warrant.aws_srp import AWSSRP


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
        step_metrics[person['username']] = {
            "steps": person['activity']['steps'],
            "minutes": person['activity']['minutes'],
            "distance": person['activity']['distance']
        }
    return step_metrics


def get_data_for_day(date_obj, token):
    # try:
    url = 'https://app.stridekick.com/graphql'
    data = {
        "operationName": "Friends",
        "query": 'query Friends($date: String, $search: String) {\n  me {\n    id\n    avatar\n    unitType\n    username\n    activity(date: $date) {\n      id\n      distance\n      minutes\n      steps\n      __typename\n    }\n    friends(search: $search) {\n      hits\n      members {\n        id\n        avatar\n        firstName\n        lastName\n        username\n        activity(date: $date) {\n          id\n          distance\n          minutes\n          steps\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    memberFriends {\n      id\n      __typename\n    }\n    __typename\n  }\n}',
        "variables":
        {
            "date": date_obj.strftime('%Y-%m-%d'),
            "search": ""
        }
    }

    headers = {
        'authorization': "Bearer " + token,
        'Apollo-Require-Preflight': 'true',
        'content-type': "application/json"
    }

    response = requests.post(url, json=data, headers=headers)
    print(json.loads(response.content))
    step_data = json.loads(response.content)['data']['me']['friends']['members']
    return format_step_data(step_data)
    # except Exception as e:
    #     print(e)
    #     return None


def scrape_fitness_metrics(usrnm, pswd, days_of_history):
    return_value = {}
    current_date = datetime.now(tz=dateutil.tz.gettz('US/Eastern'))
    token = warrant_auth(usrnm, pswd)
    if days_of_history == 0:
        date_num = current_date.strftime("%Y%m%d")
        return_value[date_num] = get_data_for_day(current_date, token)
    for i in range(days_of_history):
        selected_date = current_date - timedelta(days=i+1)
        date_num = selected_date.strftime("%Y%m%d")
        temp = get_data_for_day(selected_date, token)
        if temp:
            return_value[date_num] = temp
            print("Recieved data for " + str(date_num))
        else:
            print("Error for " + str(date_num))
    return return_value


def call_save_metrics_api(step_metrics):
    headers = {'x-api-key': os.environ['API_KEY']}
    return requests.post(os.environ['API_URL'], data=json.dumps({"step_metrics": step_metrics}), headers=headers)


def lambda_handler(event, context=None):
    days = int(event['days'])
    step_metrics = scrape_fitness_metrics(event['username'], event['password'], days_of_history=days)
    # response = call_save_metrics_api(step_metrics)
    # if response.status_code == 200:
    #     return "SUCCESS"
    # else:
    #     return "broken..."

