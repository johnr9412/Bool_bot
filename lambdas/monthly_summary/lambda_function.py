import json
import os
import requests
import boto3
import re
from datetime import datetime, timedelta


client = boto3.client('lambda', region_name='us-east-2')


def invoke_scrape_history(days):
    """Invoke scrape_history_lambda with N-day parameter, wait for it to complete."""
    payload = {
        'days': str(days),
        'username': os.environ['STRIDE_USERNAME'],
        'password': os.environ['STRIDE_PASSWORD']
    }
    response = client.invoke(
        FunctionName='scrape_history_lambda',
        Payload=json.dumps(payload),
        InvocationType='RequestResponse'
    )
    result = json.loads(response['Payload'].read())
    print(f"Scrape history result: {result}")
    return result


def get_snowflake_insights(prompt):
    """Invoke the snowflake Lambda for monthly insights."""
    response = client.invoke(
        FunctionName='load_discord_snowflake',
        Payload=json.dumps({'prompt': prompt}),
        InvocationType='RequestResponse'
    )
    result = json.loads(response['Payload'].read())
    print(f"Snowflake result: {result}")
    return result


def get_last_month_range():
    """Return (start_date, end_date) for last month."""
    now = datetime.now()
    end = now.replace(day=1) - timedelta(days=1)
    start = end.replace(day=1)
    return start, end


def split_snowflake_markdown(raw):
    """
    Split snowflake markdown response into Discord embed fields.
    Discord field value limit is 1024 chars; splits on ## headers
    and further on blank lines if a section is still too long.
    """
    DISCORD_MAX = 1024
    DISCORD_FIELD_MAX = 25

    # Split on ## headers, keeping the header as part of the chunk
    sections = re.split(r'(?=##\s)', raw.strip())
    sections = [s for s in sections if s.strip()]

    fields = []
    for section in sections:
        section = section.strip()
        # Clean up empty section titles
        title = section.split('\n')[0].strip('# ').strip()
        content = '\n'.join(line for line in section.split('\n')[1:] if line.strip())

        if not content:
            continue

        # If the content fits, use it as-is
        if len(content) <= DISCORD_MAX:
            fields.append({'name': title, 'value': content})
            continue

        # Otherwise split by blank lines and pack into chunks
        paragraphs = re.split(r'\n{2,}', content)
        buffer = ''
        for para in paragraphs:
            if len(buffer) + len(para) + 2 > DISCORD_MAX:
                if buffer:
                    fields.append({'name': title, 'value': buffer.strip()})
                title = f"{title} (cont.)"
                buffer = para + '\n'
            else:
                buffer += para + '\n'

        if buffer:
            fields.append({'name': title, 'value': buffer.strip()})

    return fields[:DISCORD_FIELD_MAX]


def create_monthly_embed(date_range, snowflake_data):
    """Build the Discord embed from date range and snowflake insights."""
    embed_fields = [{
        "name": "Date Range",
        "value": date_range,
        "inline": False
    }]

    if snowflake_data:
        fields = split_snowflake_markdown(snowflake_data)
        embed_fields.extend(fields)

    embed = {
        "title": "Monthly Step Summary",
        "color": 5814783,
        "fields": embed_fields
    }
    return embed


def send_discord_message(embed):
    """Post the embed to Discord via webhook."""
    url = os.environ['WEBHOOK']
    data = {"embeds": [embed]}
    r = requests.post(url, json=data)
    print(f"Discord response: {r.status_code}")
    return r.status_code


def lambda_handler(event, context):
    first, end = get_last_month_range()

    # 1. Scrape 90 days of history (blocking)
    invoke_scrape_history(90)

    # 2. Get snowflake insights
    prompt = f"Generate monthly step summary insights for period ending {end.strftime('%B %d, %Y')}"
    snowflake_data = get_snowflake_insights(prompt)

    # 3. Create embed
    start_str = first.strftime('%m/%d/%Y')
    end_str = end.strftime('%m/%d/%Y')
    embed = create_monthly_embed(f"{start_str} - {end_str}", snowflake_data)

    # 4. Post to Discord
    status = send_discord_message(embed)

    return {
        'statusCode': status
    }
