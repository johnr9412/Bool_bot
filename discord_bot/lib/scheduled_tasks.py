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
        #triggers the save but doesn't return values
        support_methods.get_webscrape_steps(API_URL_OBJECT['STEP_API_URL'],
                                            SECRETS_OBJECT['STEP_API_KEY'],
                                            SECRETS_OBJECT['STEPS_USERNAME'],
                                            SECRETS_OBJECT['STEPS_PASSWORD'])
    elif time.strftime('%H') == '7':
        #send message
        date_obj = datetime.today() - timedelta(days=1)
        date_num = str(date_obj.strftime("%Y%m%d"))
        response = support_methods.call_bot_lambdas(
            API_URL_OBJECT['STEP_API_URL'], SECRETS_OBJECT['STEP_API_KEY'], {
                "date_num": date_num
            })
        if response.status_code == 200:
            step_metrics = json.loads(response.content)['step_metrics']
            embed = support_methods.create_step_embed("Yesterday's Step Summary", step_metrics)
            await client.get_channel(SECRETS_OBJECT['TEST_CHANNEL_ID']).send(embed=embed)
    await client.close()


client.run(SECRETS_OBJECT['DISCORD_TOKEN'])
