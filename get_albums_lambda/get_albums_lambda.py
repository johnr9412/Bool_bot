from methods import get_albums


def lambda_handler(event, context):
    return_messages = []
    try:
        albums = get_albums.get_albums_from_playlist(event['playlist_url'], event['spotify_tokens'])
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
    except Exception as e:
        print(e)
        return_messages.append('borked. maybe the playlist link isn\'t right?')

    return return_messages
