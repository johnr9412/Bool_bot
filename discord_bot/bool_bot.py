#!/usr/bin/env python3
import json
import re
import os
import hvac
import boto3
import requests
import discord

#setup stuff
vault_client = hvac.Client(
    url=os.environ['VAULT_URL'],
    token=os.environ['VAULT_TOKEN']
)

res = vault_client.is_authenticated()
DISCORD_TOKEN = vault_client.secrets.kv.read_secret_version(path='discord_token')['data']['data']['key']
SPOTIFY_TOKEN1 = vault_client.secrets.kv.read_secret_version(path='spotify_token_1')['data']['data']['key']
SPOTIFY_TOKEN2 = vault_client.secrets.kv.read_secret_version(path='spotify_token_2')['data']['data']['key']
TEST_CHANNEL_ID = int(vault_client.secrets.kv.read_secret_version(path='test_channel_id')['data']['data']['key'])
LOCK_GUILD_ID = int(vault_client.secrets.kv.read_secret_version(path='lock_guild_id')['data']['data']['key'])
API_KEY = vault_client.secrets.kv.read_secret_version(path='api_key')['data']['data']['key']

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)


#bot events
@client.event
async def on_ready():
    #await client.get_channel(TEST_CHANNEL_ID).send('Updated. Am a brand new bot')
    await lock_server()


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
def call_bot_lambda(lambda_name, parameters):
    lambda_client = boto3.client('lambda', region_name='us-east-2')
    response = lambda_client.invoke(
        FunctionName=lambda_name,
        InvocationType='RequestResponse',
        Payload=json.dumps({'body': parameters})
    )
    return json.load(response['Payload'])


def author_authorized_for_server_actions(author):
    if author.name == 'johnr9412':
        return True
    for role in [y.name for y in author.roles]:
        if 'Moderator' in role or 'Owner' in role:
            return True
    return False


async def take_role_actions(member_records, is_lock):
    guild = client.get_guild(LOCK_GUILD_ID)
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
    guild = client.get_guild(LOCK_GUILD_ID)
    permissions_dict = {}
    for member in guild.members:
        roles = []
        for role in member.roles:
            roles.append(str(role.id))
        if len(roles) > 0:
            permissions_dict[str(member.id)] = roles

    url = 'https://qtf8017hoe.execute-api.us-east-2.amazonaws.com/test/permissions'
    myobj = json.dumps({
        "command": 'save',
        "roles": permissions_dict
    })
    headers = {'x-api-key': API_KEY}

    x = requests.post(url, data=myobj, headers=headers)

    print(x)

    if True:
        print('Permissions saved')
        #await take_role_actions(permissions_dict, is_lock=True)
        print('Permissions removed')


async def unlock_server():
    print('unlocking')
    dynamo_data = call_bot_lambda("discord_permissions_lambda", {
        "command": 'read'
    })
    member_records = dynamo_data['roles']
    #await take_role_actions(member_records, is_lock=False)
    print('Permissions updated')
    response = call_bot_lambda("discord_permissions_lambda", {
        "command": 'delete'
    })
    if response:
        print('Permissions deleted')


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
async def bot_get_albums(message):
    print('getting albums')
    response = call_bot_lambda("get_albums_lambda", {
        "playlist_url": message.content.split("playlist_albums ")[1],
        "spotify_tokens": [SPOTIFY_TOKEN1, SPOTIFY_TOKEN2]
    })
    for message_text in response:
        await message.channel.send(message_text)
        print('message sent')


async def get_schedule(message):
    print('getting schedule')
    url = re.search("(?P<url>https?://[^\s]+)", message.content).group("url")
    response = call_bot_lambda("get_schedule_lambda", {
        "schedule_url": url
    })
    previous_day = ''
    for item in response:
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
