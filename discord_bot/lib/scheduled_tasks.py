#!/usr/bin/env python3
import discord
import json
from datetime import datetime, timedelta, time
import secrets_manager as secrets_manager
import api_manager as api_manager
import support_methods as support_methods


SECRETS_OBJECT = secrets_manager.get_secrets_obj()
API_URL_OBJECT = api_manager.get_api_url_obj()


client = discord.Client()


@client.event
async def on_ready():
    if time.strftime('%H') == '23':
        save_step_snapshot()
    elif time.strftime('%H') == '7':
        await send_prev_day_summary()
    await client.close()


async def send_prev_day_summary():
    # send message
    date_obj = datetime.today() - timedelta(days=1)
    date_num = str(date_obj.strftime("%Y%m%d"))
    response = support_methods.call_bot_lambdas(
        API_URL_OBJECT['STEP_API_URL'], SECRETS_OBJECT['STEP_API_KEY'], {
            "date_num": date_num
        })
    if response.status_code == 200:
        body = json.loads(response.content)
        date_value = datetime.strptime(body['date'], '%Y%m%d').strftime('%m-%d-%Y')
        step_metrics = body['step_metrics']
        embed = support_methods.create_step_embed(
            "Yesterday's Step Summary",
            date_value,
            step_metrics)
        await client.get_channel(SECRETS_OBJECT['TEST_CHANNEL_ID']).send(embed=embed)


def save_step_snapshot():
    step_dict = support_methods.get_webscrape_steps(API_URL_OBJECT['STEP_SCRAPE_URL'],
                                                    SECRETS_OBJECT['STEP_SCRAPE_KEY'],
                                                    SECRETS_OBJECT['STEPS_USERNAME'],
                                                    SECRETS_OBJECT['STEPS_PASSWORD'])
    response = support_methods.call_bot_lambdas(
        API_URL_OBJECT['STEP_API_URL'], SECRETS_OBJECT['STEP_API_KEY'], {
            "command": 'save',
            "step_metrics": step_dict
        })
    if response.status_code == 200:
        print('Permissions saved')


client.run(SECRETS_OBJECT['DISCORD_TOKEN'])
