import decimal
import boto3
import json
import time
from boto3.dynamodb.conditions import Key


dynamodb = boto3.resource('dynamodb')
STEPS_TABLE = dynamodb.Table('step_metrics')
USERNAMES = dynamodb.Table('stridekick_crosswalk').scan()['Items']


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)


def query_table(key=None, value=None):
    if key is not None and value is not None:
        filtering_exp = Key(key).eq(value)
        return STEPS_TABLE.query(KeyConditionExpression=filtering_exp)
    raise ValueError('Parameters missing or invalid')


def get_users_name(username):
    try:
        user = next(filter(lambda x: x['stridekick_name'] == username, USERNAMES))
        return user['person_name']
    except Exception as e:
        print(e)
        return username


def format_data(data, multi_day=False):
    for i in range(len(data)):
        if isinstance(data, list):
            old_metrics = data[i]['step_metrics'].copy()
            data[i]['step_metrics'] = {}
        else:
            old_metrics = data['step_metrics'].copy()
            data['step_metrics'] = {}
        for username in old_metrics:
            person_name = get_users_name(username)
            if isinstance(data, list):
                data[i]['step_metrics'][person_name] = old_metrics[username]
            else:
                data['step_metrics'][person_name] = old_metrics[username]
    if multi_day:
        return sorted(data, key=lambda d: d['date'], reverse=True)
    else:
        return sorted(data, key=lambda d: d['timestamp'], reverse=True)


def read_step_metrics_for_day(date_num, full_history=False):
    resp = query_table(
        key='date',
        value=str(date_num)
    )
    data = format_data(resp.get('Items'), multi_day=False)
    if full_history:
        return data
    else:
        return data[0]


def read_all_step_metrics():
    response = STEPS_TABLE.scan()
    data = response['Items']
    while response.get('LastEvaluatedKey'):
        response = STEPS_TABLE.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])
    return format_data(data, multi_day=True)


def save_step_object(step_obj):
    try:
        step_obj = json.loads(json.dumps(step_obj), parse_float=decimal.Decimal)
        with STEPS_TABLE.batch_writer() as writer:
            for item in step_obj:
                writer.put_item(
                    Item={'date': str(item), 'timestamp': str(time.time()), 'step_metrics': step_obj[item]}
                )
        return True
    except Exception as e:
        print(e)
        return False


def create_response(status_code, body=None):
    response = {"statusCode": status_code}
    if body:
        response['body'] = body
    return response


def create_snowflake_response(data):
    response = {
        "statusCode": 200,
        "data": data
    }
    return response


def lambda_handler(event, context):
    try:
        http_method = event['httpMethod']
        if http_method == 'POST':
            if "sf-external-function-name" in list(event['headers'].keys()):
                response = json.dumps(create_snowflake_response(data=read_all_step_metrics()), cls=DecimalEncoder)
            else:
                body = json.loads(event['body'])
                if save_step_object(body['step_metrics']):
                    response = create_response(200)
                else:
                    print("POST 502")
                    response = create_response(502)
            return response
        elif http_method == 'GET':
            try:
                query_string = event['queryStringParameters']
                if query_string and 'date_num' in query_string:
                    date_num = event['queryStringParameters']['date_num']
                    if 'depth' in query_string:
                        return_data = read_step_metrics_for_day(date_num, full_history=True)
                    else:
                        return_data = read_step_metrics_for_day(date_num)
                    response = create_response(200, json.dumps(return_data, cls=DecimalEncoder))
                else:
                    response = create_response(200, json.dumps(read_all_step_metrics(), cls=DecimalEncoder))
            except Exception as e:
                print(e)
                response = create_response(502)
            return response
        else:
            print("Neither GET nor POST found")
            return create_response(500)
    except Exception as e:
        print(e)
        return create_response(500)
