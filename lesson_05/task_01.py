"""
Вариант I
Написать программу, которая собирает входящие письма из своего
или тестового почтового ящика и сложить данные о письмах в базу данных
(от кого, дата отправки, тема письма, текст письма полный)
    Логин тестового ящика: study.ai_172@mail.ru
    Пароль тестового ящика: NextPassword172#
"""
from pprint import pprint
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

client = MongoClient('localhost', 27017)
db = client['mail_letters']

# чтобы не открывать одни и те же письма
all_id = []
for letter_info in db.letters.find({}):
    all_id.append(letter_info['_id'])


def write_to_db(data, collection):
    """
    Записывает данные (новости) в БД
    :param data: данные (новость)
    :param collection: коллекция
    :return:
    """
    try:
        collection.insert_one(data)
    except DuplicateKeyError:
        print('Такая запись уже есть в БД')


LOGIN = 'study.ai_172@mail.ru'
PASSWORD = 'NextPassword172#'

serv = Service('./chromedriver.exe')
chrome_options = Options()
chrome_options.add_argument('start-maximized')

driver = webdriver.Chrome(service=serv, options=chrome_options)

driver.get('https://e.mail.ru/')

wait = WebDriverWait(driver, 30)

login_input = wait.until(EC.element_to_be_clickable(
    (By.XPATH, '//input[@name="username"]')
))

login_input.send_keys(LOGIN)
login_input.submit()

password_input = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, '//input[@name="password"]')
    ))
password_input.send_keys(PASSWORD)
password_input.submit()

wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'llc')))

links = set()

while True:
    sleep(0.2)  # пришлось использовать, а то некорректно срабатывал скрипт

    current_links = driver.find_elements(
        By.XPATH, '//a[contains(@class, "llc")]')

    for link in current_links:
        links.add(link.get_attribute('href'))

    actions = ActionChains(driver)
    actions.move_to_element(current_links[-1])
    actions.perform()

    try:
        driver.find_element(By.XPATH, '//a[contains(@class, "llc_last")]')
        break
    except NoSuchElementException:
        continue

print('links:', len(links))

for link in links:
    letter_data = {}

    letter_data['_id'] = link.split('0:')[1].split(':0')[0]

    # если уже есть в базе даже не открываем
    if letter_data['_id'] in all_id:
        continue

    driver.get(link)

    # от кого
    letter_author = wait.until(EC.presence_of_element_located(
        (By.CLASS_NAME, 'letter-contact')
    ))

    letter_data['author_name'] = letter_author.text
    letter_data['author_email'] = letter_author.get_attribute('title')

    # дата отправки
    letter_date = driver.find_element(By.CLASS_NAME, 'letter__date')
    letter_data['date'] = letter_date.text

    # тема письма
    letter_title = driver.find_element(By.TAG_NAME, 'h2')
    letter_data['title'] = letter_title.text

    # текст письма полный
    letter_text = driver.find_element(By.CLASS_NAME, 'letter-body__body')
    letter_data['body'] = letter_text.get_attribute('outerHTML')
    letter_data['text'] = letter_text.text

    write_to_db(letter_data, db.letters)


# Совпадает ли количество
print('links:', len(links))
print(db.letters.count_documents({}))

# for letter_info in db.letters.find({}):
#     pprint(letter_info)

# driver.close()
