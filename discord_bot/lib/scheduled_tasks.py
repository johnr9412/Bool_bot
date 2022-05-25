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
    await send_prev_day_summary()
    await client.close()


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
        await client.get_channel(SECRETS_OBJECT['TEST_CHANNEL_ID']).send(embed=embed)
    else:
        print('borked ' + str(response.status_code))


client.run(SECRETS_OBJECT['DISCORD_TOKEN'])
