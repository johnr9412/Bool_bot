import imp
import time
import json
import boto3
import psutil
import requests
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from tempfile import mkdtemp


dynamodb = boto3.resource('dynamodb', region_name="us-east-2")
USERNAMES = dynamodb.Table('stridekick_crosswalk').scan()['Items']


def start_driver(headless):
    if headless:
        options = webdriver.ChromeOptions()
        options.binary_location = '/opt/chrome/chrome'
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280x1696")
        options.add_argument("--single-process")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-dev-tools")
        options.add_argument("--no-zygote")
        options.add_argument(f"--user-data-dir={mkdtemp()}")
        options.add_argument(f"--data-path={mkdtemp()}")
        options.add_argument(f"--disk-cache-dir={mkdtemp()}")
        options.add_argument("--remote-debugging-port=9222")
        return webdriver.Chrome("/opt/chromedriver",
                                options=options)
    else:
        return webdriver.Chrome()


def login_to_site(driver, address, usrnm, pswd):
    driver.get(address)
    login_element = next(filter(lambda x: x.text == 'Log in', driver.find_elements(By.TAG_NAME, 'button')))
    login_element.click()
    fields = driver.find_elements(By.TAG_NAME, 'input')
    for el in fields:
        if el.get_attribute("name") == 'email':
            el.send_keys(usrnm)
        elif el.get_attribute("name") == 'password':
            el.send_keys(pswd)
    login_element = next(filter(lambda x: x.text == 'Login', driver.find_elements(By.TAG_NAME, 'button')))
    login_element.click()


def navigate_to_friends(driver):
    friends_url = driver.current_url + 'friends'
    driver.get(friends_url)


def get_date_num(driver):
    date_web_object = driver.find_elements(By.XPATH, '//*[@id="root"]/div[2]/div/div[2]/div/div/div[4]/div[2]/div/div/div[2]/div')[0]
    date_string = date_web_object.text.replace(',', '')
    if 'Today' in date_string:
        date_string = date_string.replace('Today ', '')
    date_object = datetime.strptime(date_string, '%b %d %Y')
    return date_object.strftime("%Y%m%d")


def get_users_name(username):
    try:
        user = next(filter(lambda x: x['stridekick_name'] == username, USERNAMES))
        return user['person_name']
    except Exception as e:
        print(e)
        return username


def get_step_data(driver):
    step_icon = driver.find_elements(By.XPATH,
                '//*[@id="root"]/div[2]/div/div[2]/div/div/div[3]/div/div/div/div[2]/div[2]/div/div[1]/i')[0]
    step_icon.click()
    step_data = {}
    tbody = driver.find_elements(By.XPATH, '//*[@id="root"]/div[2]/div/div[2]/div/div/div[4]/div[4]/div')[0]
    for user_div in filter(lambda x: x.get_attribute("class") != 'row sc-cpUXGm iffqJB',
                           tbody.find_elements(By.XPATH, "*")):
        div_objs = user_div.find_elements(By.XPATH, "*")
        user_name = div_objs[0].find_elements(By.XPATH, "./div/nobr")[0].text
        user_name = get_users_name(user_name)
        step_data[user_name] = int(div_objs[1].text.replace(",", ""))
    return step_data


def get_minute_data(driver):
    minute_icon = driver.find_elements(By.XPATH,
                '//*[@id="root"]/div[2]/div/div[2]/div/div/div[3]/div/div/div/div[2]/div[2]/div/div[2]/i')[0]
    minute_icon.click()
    minute_stats = {}
    tbody = driver.find_elements(By.XPATH, '//*[@id="root"]/div[2]/div/div[2]/div/div/div[4]/div[4]/div')[0]
    for user_div in filter(lambda x: x.get_attribute("class") != 'row sc-cpUXGm iffqJB',
                           tbody.find_elements(By.XPATH, "*")):
        div_objs = user_div.find_elements(By.XPATH, "*")
        user_name = div_objs[0].find_elements(By.XPATH, "./div/nobr")[0].text
        user_name = get_users_name(user_name)
        minute_stats[user_name] = int(div_objs[1].text.replace(",", ""))
    return minute_stats


def get_distance_data(driver):
    distance_icon = driver.find_elements(By.XPATH,
                '//*[@id="root"]/div[2]/div/div[2]/div/div/div[3]/div/div/div/div[2]/div[2]/div/div[3]/i')[0]
    distance_icon.click()
    distance_stats = {}
    tbody = driver.find_elements(By.XPATH, '//*[@id="root"]/div[2]/div/div[2]/div/div/div[4]/div[4]/div')[0]
    for user_div in filter(lambda x: x.get_attribute("class") != 'row sc-cpUXGm iffqJB',
                           tbody.find_elements(By.XPATH, "*")):
        div_objs = user_div.find_elements(By.XPATH, "*")
        user_name = div_objs[0].find_elements(By.XPATH, "./div/nobr")[0].text
        user_name = get_users_name(user_name)
        distance_stats[user_name] = float(div_objs[1].text.replace(",", ""))
    return distance_stats


def kill_chrome(driver):
    chrome_procname = "chrome" # to clean up zombie Chrome browser
    driver_procname = "chromedriver" # to clean up zombie ChromeDriver
    for proc in psutil.process_iter():
        # check whether the process name matches
        if proc.name() == chrome_procname or proc.name() == driver_procname:
            proc.kill()
    driver.quit()


def scrape_fitness_metrics(usrnm, pswd, days_of_history):
    driver = start_driver(headless=True)
    login_to_site(driver, 'https://link.stridekick.com/', usrnm, pswd)
    time.sleep(1)
    navigate_to_friends(driver)
    time.sleep(1)
    return_value = {}
    for i in range(days_of_history):
        arrow = driver.find_elements(By.XPATH, '//*[@id="root"]/div[2]/div/div[2]/div/div/div[4]/div[2]/div/div/div[1]/i')[0]
        arrow.click()
        fitness_metrics = {}
        date_num = get_date_num(driver)
        step_metrics = get_step_data(driver)
        minute_metrics = get_minute_data(driver)
        distance_metrics = get_distance_data(driver)
        for username in step_metrics:
            fitness_metrics[username] = {
                "steps": step_metrics[username],
                "minutes": minute_metrics[username],
                "distance": distance_metrics[username]
            }
        return_value[date_num] = fitness_metrics
    kill_chrome(driver)
    return return_value


def call_save_metrics_api(step_metrics):
    api_key = os.environ['API_KEY']
    print(api_key)
    api_url = os.environ['API_URL']
    print(api_url)
    headers = {'x-api-key': os.environ['API_KEY']}
    return requests.post(os.environ['API_URL'], data=json.dumps({"step_metrics": step_metrics}), headers=headers)


def lambda_handler(event, context=None):
    days = int(event['days'])
    step_metrics = scrape_fitness_metrics(event['username'], event['password'], days_of_history=days)
    response = call_save_metrics_api(step_metrics)
    if response.status_code == 200:
        return "SUCCESS"
    else:
        return "broken..."
