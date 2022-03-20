import os
import hvac


def get_secrets_obj():
    vault_client = hvac.Client(
        url=os.environ['VAULT_URL'],
        token=os.environ['VAULT_TOKEN']
    )

    res = vault_client.is_authenticated()
    return {
        "DISCORD_TOKEN": vault_client.secrets.kv.read_secret_version(
            path='discord_token')['data']['data']['key'],
        "SPOTIFY_TOKEN1": vault_client.secrets.kv.read_secret_version(
            path='spotify_token_1')['data']['data']['key'],
        "SPOTIFY_TOKEN2": vault_client.secrets.kv.read_secret_version(
            path='spotify_token_2')['data']['data']['key'],
        "TEST_CHANNEL_ID": int(vault_client.secrets.kv.read_secret_version(
            path='test_channel_id')['data']['data']['key']),
        "LOCK_GUILD_ID": int(vault_client.secrets.kv.read_secret_version(
            path='lock_guild_id')['data']['data']['key']),
        "PERMISSIONS_API_KEY": vault_client.secrets.kv.read_secret_version(
            path='permissions_api_key')['data']['data']['key'],
        "ALBUM_API_KEY": vault_client.secrets.kv.read_secret_version(
            path='album_api_key')['data']['data']['key'],
        "SCHEDULE_API_KEY": vault_client.secrets.kv.read_secret_version(
            path='schedule_api_key')['data']['data']['key']
    }
