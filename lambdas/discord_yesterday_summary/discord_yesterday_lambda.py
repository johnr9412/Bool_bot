import json
import os
import requests
from datetime import datetime, timedelta


#THIS METHOD IS ACTUAL AIDS BUT IT'S JUST HOW IT BE IDK
def transform_step_obj(step_dict):
    temp = {}
    for item in step_dict:
        step_num = int(step_dict[item]['steps'].replace(",", ""))
        step_dict[item]['steps'] = step_num
        temp[item] = step_num
    temp = {k: v for k, v in sorted(temp.items(), key=lambda x: x[1], reverse=True)}

    return_dict = {}
    for user in temp:
        return_dict[user] = step_dict[user]
    return return_dict
    
    
def create_step_embed(date_value, steps_dict):
    embed_fields = [{
        "name": "Date",
        "value": date_value,
        "inline": False
    }]
    
    count = 1
    for user in steps_dict:
        if (steps_dict[user]['steps'] + steps_dict[user]['steps'] + steps_dict[user]['steps']) > 0:
            title_text = str(count) + '. ' + user
            user_metrics = 'Steps: ' + "{:,}".format(steps_dict[user]['steps']) + '\n' \
                           + 'Miles: ' + steps_dict[user]['distance'] + '\n' \
                           + 'Minutes: ' + steps_dict[user]['minutes']
            embed_fields.append({
                "name": title_text,
                "value": user_metrics
            })
            count += 1

    embed = {
        "title": "Yesterday's Step Summary",
        "color": 3447003,
        "fields": embed_fields
    }
    return embed
    
    
def send_discord_message(step_embed):
    url = os.environ['WEBHOOK']
    data = {
        "embeds": [step_embed]
    }
    r = requests.post(url,json=data)
    print(r.status_code)


def send_prev_day_summary():
    date_obj = datetime.today() - timedelta(days=1)
    param_obj = {
            "date_num": str(date_obj.strftime("%Y%m%d"))
        }
    headers = {'x-api-key': os.environ['STEP_API_KEY']}
    response = requests.get(os.environ['STEP_API_URL'], params=param_obj, headers=headers)

    if response.status_code == 200:
        body = json.loads(response.content)
        date_value = datetime.strptime(body['date'], '%Y%m%d').strftime('%m-%d-%Y')
        step_metrics = transform_step_obj(body['step_metrics'])

        embed = create_step_embed(date_value, step_metrics)

        send_discord_message(embed)
    else:
        print('There was an issue')
        print('Status Code: ' + str(response.status_code))


def lambda_handler(event, context):
    send_prev_day_summary()
    return {
        'statusCode': 200
    }
