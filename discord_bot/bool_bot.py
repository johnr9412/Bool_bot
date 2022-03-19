#!/usr/bin/env python3
import json
import re
import requests
import discord
from lib import secrets_manager

#setup stuff
SECRETS_OBJECT = secrets_manager.get_secrets_obj()

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)


#bot events
@client.event
async def on_ready():
    await client.get_channel(SECRETS_OBJECT['TEST_CHANNEL_ID']).send('Updated. Am a brand new bot')


@client.event
async def on_message(message):
    if client.user.mentioned_in(message):
        message_content = message.content.lower()
        regex = r'\b(\w+ing)\b'
        if re.search(regex, message_content):
            word = re.findall(regex, message_content)[0]
            await message.channel.send(word.replace("ing", "ong").upper())
        elif 'lock' in message_content and author_authorized_for_server_actions(message.author):
            if '-lock' in message_content:
                await lock_server()
                await message.channel.send('Roles removed')
            elif '-unlock' in message_content:
                await unlock_server()
                await message.channel.send('Roles replaced')
        elif 'playlist_albums' in message_content:
            await bot_get_albums(message)
    elif 'https://clashfinder.com/m/' in message.content or 'https://clashfinder.com/s/' in message.content:
        await get_schedule(message)


#user defined functions
def call_bot_lambdas(lambda_key_base, param_obj):
    url_key_selector = lambda_key_base + '_URL'
    api_key_selector = lambda_key_base + '_KEY'
    headers = {'x-api-key': SECRETS_OBJECT[api_key_selector]}
    return requests.post(SECRETS_OBJECT[url_key_selector], data=json.dumps(param_obj), headers=headers)


def author_authorized_for_server_actions(author):
    if author.name == 'johnr9412':
        return True
    for role in [y.name for y in author.roles]:
        if 'Moderator' in role or 'Owner' in role:
            return True
    return False


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


#async functions
async def take_role_actions(member_records, is_lock):
    guild = client.get_guild(SECRETS_OBJECT['LOCK_GUILD_ID'])
    server_roles = guild.roles
    server_members = guild.members
    for member_id in member_records:
        member = next(filter(lambda s_member: s_member.id == int(member_id), server_members), None)
        member_roles = list(filter(lambda s_role: str(s_role.id) in member_records[member_id], server_roles))
        if member is not None and len(member_roles) > 0:
            try:
                if is_lock:
                    await member.remove_roles(*member_roles)
                else:
                    await member.add_roles(*member_roles)
            except Exception as e:
                print(e)
            print(member.name)


async def lock_server():
    print('locking')
    guild = client.get_guild(SECRETS_OBJECT['LOCK_GUILD_ID'])
    permissions_dict = {}
    for member in guild.members:
        roles = []
        for role in member.roles:
            roles.append(str(role.id))
        if len(roles) > 0:
            permissions_dict[str(member.id)] = roles

    response = call_bot_lambdas('PERMISSIONS_API', {
        "command": 'save',
        "roles": permissions_dict
    })
    if response.status_code == 200:
        print('Permissions saved')
        await take_role_actions(permissions_dict, is_lock=True)
        print('Permissions removed')


async def unlock_server():
    print('unlocking')
    response = call_bot_lambdas('PERMISSIONS_API', {
        "command": 'read'
    })
    if response.status_code == 200:
        member_records = json.loads(response.content)['roles']
        await take_role_actions(member_records, is_lock=False)
        print('Permissions updated')
        response = call_bot_lambdas('PERMISSIONS_API', {
            "command": 'delete'
        })
        if response.status_code == 200:
            print('Permissions deleted')


async def bot_get_albums(message):
    print('getting albums')
    response = call_bot_lambdas('ALBUM_API', {
        "playlist_url": message.content.split("playlist_albums ")[1],
        "spotify_tokens": [SECRETS_OBJECT['SPOTIFY_TOKEN1'], SECRETS_OBJECT['SPOTIFY_TOKEN2']]
    })
    if response.status_code == 200:
        for message_text in json.loads(response.content):
            await message.channel.send(message_text)
    else:
        await message.channel.send(response.content)


async def get_schedule(message):
    print('getting schedule')
    url = re.search("(?P<url>https?://[^\s]+)", message.content).group("url")
    response = call_bot_lambdas('SCHEDULE_API', {
        "schedule_url": url
    })
    if response.status_code == 200:
        previous_day = ''
        for item in json.loads(response.content):
            json_item = json.loads(item)
            day = json_item['day']
            if previous_day == day:
                previous_day = day
                day += ' Cont.'
            else:
                previous_day = day
            await message.channel.send(embed=create_embed(item, day))
    else:
        await message.channel.send('Something went wrong')


#start the bot
client.run(SECRETS_OBJECT['DISCORD_TOKEN'])
