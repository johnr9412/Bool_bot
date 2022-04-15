import requests
import json
from datetime import datetime
from discord import embeds, colour


def call_bot_lambdas(api_url, api_key, param_obj):
    headers = {'x-api-key': api_key}
    return requests.post(api_url, data=json.dumps(param_obj), headers=headers)


def author_authorized_for_server_actions(author):
    if author.name == 'johnr9412':
        return True
    for role in [y.name for y in author.roles]:
        if 'Moderator' in role or 'Owner' in role:
            return True
    return False


def create_schedule_embed(item, day):
    embed = embeds.Embed(title=day, color=colour.Color.blue())
    dictionary = json.loads(item)['stage_schedules']
    stage_names = list(dictionary)
    for stage in stage_names:
        artist_string = ''
        for artist in dictionary[stage]['shows']:
            artist_string += artist + '\n'
        embed.add_field(name=stage, value=artist_string,
                        inline=True)
    return embed


def create_step_embed(caption, steps_dict):
    embed = embeds.Embed(title=caption, color=colour.Color.blue())
    embed.add_field(name='Date Stamp', value=datetime.today().strftime('%m-%d-%Y'), inline=False)
    message_text = ''
    for item in steps_dict:
        message_text += (item + ': ' + str(steps_dict[item]) + '\n')
    embed.add_field(name='Step Counts', value=message_text, inline=False)
    embed.add_field(name='Something motivational', value='Today is the day that yall will kill it and here is more shit', inline=False)
    return embed
