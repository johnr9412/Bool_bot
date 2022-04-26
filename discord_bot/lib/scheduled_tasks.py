#!/usr/bin/env python3
import discord
import json
import dateutil.tz
from datetime import datetime, timedelta
import secrets_manager as secrets_manager
import api_manager as api_manager
import support_methods as support_methods


SECRETS_OBJECT = secrets_manager.get_secrets_obj()
API_URL_OBJECT = api_manager.get_api_url_obj()


client = discord.Client()


@client.event
async def on_ready():
    hour = datetime.now(tz=dateutil.tz.gettz('US/Eastern')).strftime('%H')
    if hour == '23':
        save_step_snapshot()
    elif hour == '07':
        await send_prev_day_summary()
    await client.close()


def save_step_snapshot():
    print('getting metrics')
    step_dict = support_methods.get_webscrape_data(API_URL_OBJECT['STEP_SCRAPE_URL'],
                                                   SECRETS_OBJECT['STEP_SCRAPE_KEY'],
                                                   SECRETS_OBJECT['STEPS_USERNAME'],
                                                   SECRETS_OBJECT['STEPS_PASSWORD'],
                                                   full_metrics=True)
    print("metrics received")
    if step_dict['success']:
        response = support_methods.call_bot_api_post_method(
            API_URL_OBJECT['STEP_API_URL'], SECRETS_OBJECT['STEP_API_KEY'], {
                "step_metrics": step_dict['metrics']
            })
        if response.status_code == 200:
            print('Metrics saved')
        else:
            print("borked " + str(response.status_code))


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


async def send_prev_day_summary():
    date_obj = datetime.today() - timedelta(days=1)
    date_num = str(date_obj.strftime("%Y%m%d"))
    response = support_methods.call_bot_api_get_method(
        API_URL_OBJECT['STEP_API_URL'], SECRETS_OBJECT['STEP_API_KEY'], param_obj={
            "date_num": date_num
        })
    if response.status_code == 200:
        body = json.loads(response.content)
        date_value = datetime.strptime(body['date'], '%Y%m%d').strftime('%m-%d-%Y')
        step_metrics = transform_step_obj(body['step_metrics'])
        embed = support_methods.create_full_metrics_embed(
            "Yesterday's Step Summary",
            date_value,
            step_metrics)
        await client.get_channel(SECRETS_OBJECT['HEALTH_CHANNEL_ID']).send(embed=embed)
    else:
        print('borked ' + str(response.status_code))


client.run(SECRETS_OBJECT['DISCORD_TOKEN'])
