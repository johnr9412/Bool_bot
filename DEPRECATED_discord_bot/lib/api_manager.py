
PERMISSIONS_API_URL = 'https://83odmhhpre.execute-api.us-east-2.amazonaws.com/default/discord_permissions_lambda'
ALBUMS_API_URL = 'https://69vs2jybyc.execute-api.us-east-2.amazonaws.com/default/get_albums_lambda'
SCHEDULE_API_URL = 'https://w53anzeyii.execute-api.us-east-2.amazonaws.com/default/get_schedule_lambda'
STEP_SCRAPE_URL = 'https://8dq3a5fp5a.execute-api.us-east-2.amazonaws.com/default/step_scraper_lambda'
STEP_API_URL = 'https://9m28i4tgoc.execute-api.us-east-2.amazonaws.com/default/step_data_lambda'
COUNTDOWN_API_URL = 'https://a1bj4owdbe.execute-api.us-east-2.amazonaws.com/default/event_countdown_lambda'


def get_api_url_obj():
    return {
        "PERMISSIONS_API_URL": PERMISSIONS_API_URL,
        "ALBUMS_API_URL": ALBUMS_API_URL,
        "SCHEDULE_API_URL": SCHEDULE_API_URL,
        "STEP_SCRAPE_URL": STEP_SCRAPE_URL,
        "STEP_API_URL": STEP_API_URL,
        "COUNTDOWN_API_URL": COUNTDOWN_API_URL
    }
