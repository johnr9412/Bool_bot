import json
from methods import get_albums


def create_response(status_code, body):
    response = {
        "statusCode": status_code,
        "body": json.dumps(body)
    }
    return response


def lambda_handler(event, context):
    try:
        return_messages = []
        event_body = json.loads(event['body'])
        print(event_body['playlist_url'])
        albums = get_albums.get_albums_from_playlist(event_body['playlist_url'], event_body['spotify_tokens'])
        message_builder = ''
        counter = 0
        for i in range(len(albums)):
            if i < len(albums) - 1:
                if counter < 20:
                    message_builder = message_builder + albums[i] + '\n'
                    counter += 1
                else:
                    counter = 0
                    message_content = message_builder + albums[i]
                    message_builder = ''
                    return_messages.append(message_content)
            else:
                message_content = message_builder + albums[i]
                return_messages.append(message_content)
        return create_response(200, return_messages)
    except Exception as e:
        print(e)
        return create_response(500, 'borked. maybe the playlist link isn\'t right?')
