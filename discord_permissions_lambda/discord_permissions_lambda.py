import boto3
import time
import json

PERMISSIONS_TABLE = boto3.resource('dynamodb').Table('discord_permissions')

IGNORE_ROLES = [
    '644996941729497088',
    '691124748746489938',
    '645007257750470697',
    '645008107411472405',
    '946505159255683095',
    '940749928743964674',
    '645022873706299470',
    '946492281828040754'
]


def save_permissions(permissions_dict):
    permissions_dict = {i: [a for a in j if a not in IGNORE_ROLES] for i, j in permissions_dict.items()}
    try:
        ts = time.time()
        PERMISSIONS_TABLE.put_item(Item={'timestamp': str(ts), 'roles': permissions_dict})
        return True
    except Exception as e:
        print(e)
        return False


def read_permissions():
    response = PERMISSIONS_TABLE.scan()
    data = response['Items']
    while response.get('LastEvaluatedKey'):
        response = PERMISSIONS_TABLE.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])
    return sorted(data, key=lambda d: d['timestamp'], reverse=True)[0]


def delete_permissions_records():
    try:
        data = read_permissions()
        PERMISSIONS_TABLE.delete_item(Key={'timestamp': data['timestamp']})
        return True
    except Exception as e:
        print(e)
        return False


def create_response(status_code, body=None):
    if body:
        return {
            "statusCode": status_code,
            "body": body
        }
    else:
        return {
            "statusCode": status_code
        }


def lambda_handler(event, context):
    command = json.loads(event['body'])['command']
    if command == 'read':
        response = create_response(200, json.dumps(read_permissions()))
    elif command == 'save':
        if save_permissions(json.loads(event['body'])['roles']):
            response = create_response(200)
        else:
            response = create_response(500)
    elif command == 'delete':
        if delete_permissions_records():
            response = create_response(200)
        else:
            response = create_response(500)
    else:
        response = create_response(500)

    return response
