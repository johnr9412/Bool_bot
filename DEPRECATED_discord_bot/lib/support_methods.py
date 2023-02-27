import requests
import json
from discord import embeds, colour


def call_bot_api_post_method(api_url, api_key, param_obj):
    headers = {'x-api-key': api_key}
    return requests.post(api_url, data=json.dumps(param_obj), headers=headers)


def call_bot_api_get_method(api_url, api_key, param_obj=None):
    headers = {'x-api-key': api_key}
    if param_obj:
        return requests.get(api_url, params=param_obj, headers=headers)
    else:
        return requests.get(api_url, headers=headers)


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


def get_webscrape_data(step_url, step_key, username, password):
    try:
        response = call_bot_api_post_method(
            step_url, step_key, {
                "username": username,
                "password": password
            })
        if response.status_code == 200:
            return {
                "success": True,
                "metrics": json.loads(response.content)
            }
        else:
            return {
                "success": False
            }
    except Exception as e:
        print(e)
        return {
            "success": False
        }
