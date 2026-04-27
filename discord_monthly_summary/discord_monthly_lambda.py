import os
import json
import snowflake.connector as sc
import boto3
from botocore.exceptions import ClientError
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


def get_secret():
    secret_name = "prod/bool_bot/monthly_agent"
    region_name = "us-east-2"
    
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e
    return json.loads(get_secret_value_response['SecretString'])


def build_conn_params():
    secret_dict = get_secret()

    p_key = serialization.load_pem_private_key(
        secret_dict['privateKey'].encode(),
        password=None,
        backend=default_backend()
    )

    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    return {
        "user": secret_dict['user'],
        "account": secret_dict['account'],
        "private_key": pkb,
        "warehouse": os.getenv('WAREHOUSE'),
        "database": os.getenv('DATABASE'),
        "schema": os.getenv('SCHEMA')
    }


def lambda_handler(event=None, context=None):
    conn_params = build_conn_params()
    ctx = sc.connect(**conn_params)
    cursor = ctx.cursor()
    cursor.execute("SELECT JOHN_DB.PUBLIC.STEPS_AGENT_MONTHLY_INVOKE('How many steps did John take last month?')")
    results = cursor.fetchone()
    print(results)

lambda_handler()