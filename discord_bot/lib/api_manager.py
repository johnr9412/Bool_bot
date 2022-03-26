
PERMISSIONS_API_URL = 'https://83odmhhpre.execute-api.us-east-2.amazonaws.com/default/discord_permissions_lambda'
ALBUMS_API_URL = 'https://r54yt5jv97.execute-api.us-east-2.amazonaws.com/default/get_albums_lambda'
SCHEDULE_API_URL = 'https://w53anzeyii.execute-api.us-east-2.amazonaws.com/default/get_schedule_lambda'


def get_api_url_obj():
    return {
        "PERMISSIONS_API_URL": PERMISSIONS_API_URL,
        "ALBUMS_API_URL": ALBUMS_API_URL,
        "SCHEDULE_API_URL": SCHEDULE_API_URL
    }
