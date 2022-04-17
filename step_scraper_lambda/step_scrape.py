import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from tempfile import mkdtemp


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


def get_step_data(driver):
    user_stats = {}
    tbody = driver.find_element(By.TAG_NAME, 'tbody')
    for user_div in filter(lambda x: x.get_attribute("class") != 'row sc-iDtgLy jTKDPk', tbody.find_elements(By.XPATH, "*")):
        div_objs = user_div.find_elements(By.XPATH, "*")
        user_name = div_objs[0].find_elements(By.XPATH, "./div/nobr")[0].text
        steps = int(div_objs[1].text.replace(",", ""))
        user_stats[user_name] = steps
    return user_stats


def get_steps(usrnm, pswd):
    driver = start_driver(headless=True)
    login_to_site(driver, 'https://link.stridekick.com/', usrnm, pswd)
    time.sleep(1)
    navigate_to_friends(driver)
    time.sleep(1)
    step_dict = get_step_data(driver)
    driver.close()
    return step_dict


def lambda_handler(event, context=None):
    body = json.loads(event['body'])
    return {
        'statusCode': 200,
        'body': json.dumps(get_steps(body['username'], body['password']))
    }
