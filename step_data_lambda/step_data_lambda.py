import decimal
import boto3
import json
import time
from boto3.dynamodb.conditions import Key


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)


def query_table(key=None, value=None):
    step_table = boto3.resource('dynamodb').Table('step_metrics')
    if key is not None and value is not None:
        filtering_exp = Key(key).eq(value)
        return step_table.query(KeyConditionExpression=filtering_exp)
    raise ValueError('Parameters missing or invalid')


def read_step_metrics(date_num):
    resp = query_table(
        key='date',
        value=date_num
    )
    data = resp.get('Items')
    return sorted(data, key=lambda d: d['timestamp'], reverse=True)[0]


def save_step_object(step_obj):
    try:
        step_obj = json.loads(json.dumps(step_obj), parse_float=decimal.Decimal)
        table = boto3.resource('dynamodb').Table('step_metrics')
        for item in step_obj:
            ts = time.time()
            table.put_item(Item={'date': str(item), 'timestamp': str(ts), 'step_metrics': step_obj[item]})
        return True
    except Exception as e:
        print(e)
        return False


def create_response(status_code, body=None):
    response = {"statusCode": status_code}
    if body:
        response['body'] = body
    return response


def lambda_handler(event, context):
    try:
        http_method = event['httpMethod']
        if http_method == 'POST':
            body = json.loads(event['body'])
            if save_step_object(body['step_metrics']):
                response = create_response(200)
            else:
                response = create_response(502)
            return response
        elif http_method == 'GET':
            try:
                date_num = event['queryStringParameters']['date_num']
                response = create_response(200, json.dumps(read_step_metrics(date_num), cls=DecimalEncoder))
            except Exception as e:
                print(e)
                response = create_response(502)
            return response
        else:
            return create_response(500)
    except Exception as e:
        print(e)
        return create_response(500)
