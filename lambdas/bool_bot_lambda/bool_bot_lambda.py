import json
import boto3
import os

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

PING_PONG = {"type": 1}
RESPONSE_TYPES = {
    "PONG": 1,
    "ACK_NO_SOURCE": 2,
    "MESSAGE_NO_SOURCE": 3,
    "MESSAGE_WITH_SOURCE": 4,
    "ACK_WITH_SOURCE": 5
}


def verify_signature(event):
    raw_body = event.get("rawBody")
    auth_sig = event['params']['header'].get('x-signature-ed25519')
    auth_ts = event['params']['header'].get('x-signature-timestamp')

    message = auth_ts.encode() + raw_body.encode()
    verify_key = VerifyKey(bytes.fromhex(os.environ['PUBLIC_KEY']))
    verify_key.verify(message, bytes.fromhex(auth_sig))  # raises an error if unequal


def ping_pong(body):
    if body.get("type") == 1:
        return True
    return False


def get_event_countdown(event_name):
    data = {'action': 'GET', 'event_name': event_name}
    client = boto3.client('lambda')
    response = client.invoke(
        FunctionName='event_countdown_lambda',
        InvocationType='RequestResponse',
        Payload=json.dumps(data)
    )
    return json.loads(response.get('Payload').read())


def get_steps(app_id, token):
    data = {
        'username': os.environ['USERNAME'],
        'password': os.environ['PASSWORD'],
        'app_id': app_id,
        'token': token
    }
    client = boto3.client('lambda')
    client.invoke(
        FunctionName='step_scraper_lambda',
        InvocationType='Event',
        Payload=json.dumps(data)
    )


def lambda_handler(event, context):
    print(event)  # debug print
    # verify the signature
    try:
        verify_signature(event)
    except Exception as e:
        raise Exception(f"[UNAUTHORIZED] Invalid request signature: {e}")

    # check if message is a ping
    body = event.get('body-json')
    if ping_pong(body):
        return PING_PONG

    name = body['data']['name']
    if name == 'countdown':
        event_name = body['data']['options'][0]['value']
        response = get_event_countdown(event_name)
        return {
            "type": RESPONSE_TYPES['MESSAGE_WITH_SOURCE'],
            "data": {
                "tts": False,
                "content": response,
                "embeds": [],
                "allowed_mentions": []
            }
        }
    elif name == 'get-steps':

        app_id = body['application_id']
        token = body['token']
        get_steps(app_id, token)
        return {
            "type": RESPONSE_TYPES['ACK_WITH_SOURCE'],
            "data": {
                "tts": False,
                "content": "",
                "embeds": [],
                "allowed_mentions": []
            }
        }

    # dummy return
    return {
        "type": RESPONSE_TYPES['MESSAGE_NO_SOURCE'],
        "data": {
            "tts": False,
            "content": "BEEP BOOP",
            "embeds": [],
            "allowed_mentions": []
        }
    }