import time
import json
import boto3
import psutil
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


def get_users_name(username):
    try:
        user = next(filter(lambda x: x['stridekick_name'] == username, USERNAMES))
        return user['person_name']
    except Exception as e:
        print(e)
        return username


def get_step_data(driver):
    step_data = {}
    tbody = driver.find_elements(By.XPATH, '//*[@id="root"]/div[2]/div/div[2]/div/div/div[4]/div[4]/div')[0]
    for user_div in filter(lambda x: x.get_attribute("class") != 'row sc-SjVdP dSgNda',
                           tbody.find_elements(By.XPATH, "*")):
        div_objs = user_div.find_elements(By.XPATH, "*")
        user_name = div_objs[0].find_elements(By.XPATH, "./div/nobr")[0].text
        user_name = get_users_name(user_name)
        step_data[user_name] = int(div_objs[1].get_attribute('innerHTML').replace(",", ""))
    return step_data


def kill_chrome(driver):
    # to clean up zombie Chrome browser
    chrome_procname = "chrome"
    # to clean up zombie ChromeDriver
    driver_procname = "chromedriver"
    for proc in psutil.process_iter():
        # check whether the process name matches
        if proc.name() == chrome_procname or proc.name() == driver_procname:
            proc.kill()
    driver.quit()


def scrape_fitness_metrics(usrnm, pswd):
    driver = start_driver(headless=True)
    login_to_site(driver, 'https://link.stridekick.com/', usrnm, pswd)
    time.sleep(1)
    navigate_to_friends(driver)
    time.sleep(1)
    step_metrics = get_step_data(driver)
    kill_chrome(driver)
    return step_metrics


def lambda_handler(event, context=None):
    try:
        body = json.loads(event['body'])
        return {
            'statusCode': 200,
            'body': json.dumps(scrape_fitness_metrics(body['username'], body['password']))
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500
        }
