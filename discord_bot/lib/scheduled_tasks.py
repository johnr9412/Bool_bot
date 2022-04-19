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
    elif hour == '14':
        await send_prev_day_summary()
    await client.close()


def save_step_snapshot():
    step_dict = support_methods.get_webscrape_steps(API_URL_OBJECT['STEP_SCRAPE_URL'],
                                                    SECRETS_OBJECT['STEP_SCRAPE_KEY'],
                                                    SECRETS_OBJECT['STEPS_USERNAME'],
                                                    SECRETS_OBJECT['STEPS_PASSWORD'])
    if step_dict['success']:
        response = support_methods.call_bot_lambdas(
            API_URL_OBJECT['STEP_API_URL'], SECRETS_OBJECT['STEP_API_KEY'], {
                "command": 'save',
                "step_metrics": step_dict['steps']
            })
        if response.status_code == 200:
            print('Steps saved')
        else:
            print("borked")


def transform_step_obj(step_dict):
    for item in step_dict:
        step_dict[item] = int(step_dict[item].replace(",", ""))
    return {k: v for k, v in sorted(step_dict.items(), key=lambda x: x[1], reverse=True)}


async def send_prev_day_summary():
    date_obj = datetime.today() - timedelta(days=1)
    date_num = str(date_obj.strftime("%Y%m%d"))
    response = support_methods.call_bot_lambdas(
        API_URL_OBJECT['STEP_API_URL'], SECRETS_OBJECT['STEP_API_KEY'], {
            "command": "read",
            "date_num": date_num
        })
    if response.status_code == 200:
        body = json.loads(response.content)
        date_value = datetime.strptime(body['date'], '%Y%m%d').strftime('%m-%d-%Y')
        step_metrics = transform_step_obj(body['step_metrics'])
        embed = support_methods.create_step_embed(
            "Yesterday's Step Summary",
            date_value,
            step_metrics)
        await client.get_channel(SECRETS_OBJECT['TEST_CHANNEL_ID']).send(embed=embed)
    else:
        print('borked')


client.run(SECRETS_OBJECT['DISCORD_TOKEN'])
