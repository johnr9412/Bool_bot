import decimal
import boto3
import json
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


def lambda_handler(event, context):
    date_num = json.loads(event['body'])['date_num']
    return {
        "statusCode": 200,
        "body": json.dumps(read_step_metrics(date_num), cls=DecimalEncoder)
    }
