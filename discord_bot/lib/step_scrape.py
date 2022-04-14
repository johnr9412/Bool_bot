import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


def start_driver(headless):
    if headless:
        options = Options()
        options.add_argument("headless")
        options.add_argument("disable-gpu")
        options.BinaryLocation = "/usr/bin/chromium-browser"
        return webdriver.Chrome(options=options)
    else:
        return webdriver.Chrome()


DRIVER = start_driver(headless=True)


def login_to_site(address, usrnm, pswd):
    DRIVER.get(address)
    login_element = next(filter(lambda x: x.text == 'Log in', DRIVER.find_elements(By.TAG_NAME, 'button')))
    login_element.click()
    fields = DRIVER.find_elements(By.TAG_NAME, 'input')
    for el in fields:
        if el.get_attribute("name") == 'email':
            el.send_keys(usrnm)
        elif el.get_attribute("name") == 'password':
            el.send_keys(pswd)
    login_element = next(filter(lambda x: x.text == 'Login', DRIVER.find_elements(By.TAG_NAME, 'button')))
    login_element.click()


def navigate_to_friends():
    friends_url = DRIVER.current_url + 'friends'
    DRIVER.get(friends_url)


def get_step_data():
    user_stats = {}
    tbody = DRIVER.find_element(By.TAG_NAME, 'tbody')
    for user_div in filter(lambda x: x.get_attribute("class") != 'row sc-iDtgLy jTKDPk', tbody.find_elements(By.XPATH, "*")):
        div_objs = user_div.find_elements(By.XPATH, "*")
        user_name = div_objs[0].find_elements(By.XPATH, "./div/nobr")[0].text
        steps = int(div_objs[1].text.replace(",", ""))
        user_stats[user_name] = steps
    return user_stats


def get_steps(usrnm, pswd):
    login_to_site('https://link.stridekick.com/', usrnm, pswd)
    time.sleep(1)
    navigate_to_friends()
    time.sleep(1)
    step_dict = get_step_data()
    DRIVER.close()
    return step_dict
