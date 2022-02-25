#!/usr/bin/env python3

import json
import re
import os
import hvac
import boto3
import discord

#setup stuff
client = hvac.Client(
    url=os.environ['VAULT_URL'],
    token=os.environ['VAULT_TOKEN']
)

res = client.is_authenticated()
DISCORD_TOKEN = client.secrets.kv.read_secret_version(path='discord_token')['data']['data']['key']
SPOTIFY_TOKEN1 = client.secrets.kv.read_secret_version(path='spotify_token_1')['data']['data']['key']
SPOTIFY_TOKEN2 = client.secrets.kv.read_secret_version(path='spotify_token_2')['data']['data']['key']
TEST_GUILD = 'jrrobinson\'s nonsense server'

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)


#bot events
@client.event
async def on_ready():
    #send message in Test
    for guild_item in client.guilds:
        if guild_item.name == TEST_GUILD:
            for channel in guild_item.channels:
                if channel.name == 'testing':
                    await channel.send('Updated. Am a brand new bot')


@client.event
async def on_message(message):
    if client.user.mentioned_in(message):
        regex = r'\b(\w+ing)\b'
        if re.search(regex, message.content):
            word = re.findall(regex, message.content)[0]
            await message.channel.send(word.replace("ing", "ong").upper())
        elif 'playlist_albums' in message.content:
            await bot_get_albums(message)
    elif 'https://clashfinder.com/m/' in message.content or 'https://clashfinder.com/s/' in message.content:
        await get_schedule(message)


#user defined functions
def call_bot_lambda(lambda_name, parameters):
    lambda_client = boto3.client('lambda', region_name='us-east-2')
    response = lambda_client.invoke(
        FunctionName=lambda_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(parameters)
    )
    return response


async def bot_get_albums(message):
    print('getting albums')
    response = call_bot_lambda("get_albums_lambda", {
        "playlist_url": message.content.split("playlist_albums ")[1],
        "spotify_tokens": [SPOTIFY_TOKEN1, SPOTIFY_TOKEN2]
    })
    for message_text in json.load(response['Payload']):
        await message.channel.send(message_text)
        print('message sent')


def create_embed(item, day):
    embed = discord.Embed(title=day, color=discord.Color.blue())
    dictionary = json.loads(item)['stage_schedules']
    stage_names = list(dictionary)
    for stage in stage_names:
        artist_string = ''
        for artist in dictionary[stage]['shows']:
            artist_string += artist + '\n'
        embed.add_field(name=stage, value=artist_string,
                        inline=True)
    return embed


async def get_schedule(message):
    print('getting schedule')
    url = re.search("(?P<url>https?://[^\s]+)", message.content).group("url")
    response = call_bot_lambda("get_schedule_lambda", {
        "schedule_url": url
    })
    previous_day = ''
    for item in json.load(response['Payload']):
        json_item = json.loads(item)
        day = json_item['day']
        if previous_day == day:
            previous_day = day
            day += ' Cont.'
        else:
            previous_day = day
        await message.channel.send(embed=create_embed(item, day))


#start the bot
client.run(DISCORD_TOKEN)
