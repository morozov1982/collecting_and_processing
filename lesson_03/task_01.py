import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# https://hh.kz/search/vacancy?area=160&search_field=name&search_field=description&text=Python&clusters=true&ored_clusters=true&enable_snippets=true&page=1&hhtmFrom=vacancy_search_list
base_url = 'https://hh.kz'
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36'}
current_url = base_url + '/search/vacancy'

client = MongoClient('localhost', 27017)
db = client['hh']

current_page = 1
num_pages = 0

params = {'area': '160',
          'search_field': ('name', 'description'),
          'text': 'Python',
          'clusters': 'true',
          'ored_clusters': 'true',
          'enable_snippets': 'true',
          'page': current_page,
          'hhtmFrom': 'vacancy_search_list'}

vacancy_list = []


def write_vacancy_to_db(vacancy, collection):
    """
    Записывает вакансию в коллекцию в БД
    :param vacancy: вакансия
    :param collection: коллекция
    :return:
    """
    try:
        collection.insert_one(vacancy)
    except DuplicateKeyError:
        # устал читать в консоли ;-)
        # print('Такая запись уже есть в БД')
        pass


def print_vacancies_greater_than(salary, collection):
    """
    Ищет и выводит на экран вакансии с заработной платой больше введённой суммы
    :param salary: зарплата
    :param collection: коллекция
    :return: None
    """
    result = collection.find({'$or': [
        {'salary_from': {
            '$gt': salary
        }
        },
        {'salary_to': {
            '$ne': None,
            '$gt': salary
        },
        }
    ]})

    for el in result:
        print(el)


def parse_vacancy_compensation(data: str) -> dict:
    """
    Принимает строку с зарплатой,
    возвращает словарь с размером зарплаты (от, до) и наименование валюты
    :param data: строка с данными о зарплате
    :return: словарь с данными о размерах и валюте зарплаты
    """
    data = data.replace('\u202f', '')

    data_from = None
    data_to = None
    data_currency = None

    if '–' in data:
        data_from, data_to = data.split(' – ')
        data_to, data_currency = data_to.split(' ')
    elif 'от' in data:
        _, data_from, data_currency = data.split(' ')
    elif 'до' in data:
        _, data_to, data_currency = data.split(' ')

    if data_from:
        data_from = int(data_from)
    if data_to:
        data_to = int(data_to)

    return {'salary_from': data_from, 'salary_to': data_to,
            'currency': data_currency}


while True:
    params['page'] = current_page
    response = requests.get(current_url, headers=headers, params=params)

    if response.ok:
        dom = BeautifulSoup(response.text, 'html.parser')

        if not num_pages or num_pages == 0:
            pager = dom.find('div', {'class': 'pager'})
            last_page_btn = pager.findChildren('span', recursive=False)[-1]
            num_pages = last_page_btn.find('span').get_text()
            num_pages = int(num_pages)

        vacancy_items = dom.select('div.vacancy-serp-item')

        for item in vacancy_items:
            vacancy_data = {}

            vacancy_compensation = {'salary_from': None, 'salary_to': None,
                                    'currency': None}
            vacancy_employer = None
            vacancy_city = None

            vacancy_title = item.find('a', {
                'data-qa': 'vacancy-serp__vacancy-title'})

            vacancy_name = vacancy_title.text
            vacancy_link = vacancy_title['href']
            vacancy_link = vacancy_link.split('?')[0]  # как вариант

            vacancy_id = vacancy_link.split('/')[-1]

            vacancy_compensation_data = item.find('span', {
                'data-qa': 'vacancy-serp__vacancy-compensation'})

            if vacancy_compensation_data:
                vacancy_compensation = parse_vacancy_compensation(
                    vacancy_compensation_data.text)

            vacancy_employer_tag = item.find('a', {
                'data-qa': 'vacancy-serp__vacancy-employer'})
            if vacancy_employer_tag:
                vacancy_employer = vacancy_employer_tag.get_text(' ',
                                                                 strip=True)

            vacancy_city_div = item.find('div', {
                'data-qa': 'vacancy-serp__vacancy-address'})
            vacancy_city = vacancy_city_div.get_text()

            vacancy_data['_id'] = vacancy_id
            vacancy_data['title'] = vacancy_name
            vacancy_data['link'] = vacancy_link
            vacancy_data['salary_from'] = vacancy_compensation['salary_from']
            vacancy_data['salary_to'] = vacancy_compensation['salary_to']
            vacancy_data['currency'] = vacancy_compensation['currency']
            vacancy_data['site'] = base_url
            vacancy_data['employer'] = vacancy_employer
            vacancy_data['city'] = vacancy_city

            vacancy_list.append(vacancy_data)

        current_page += 1
        if current_page > num_pages:
            break
    else:
        break

for item in vacancy_list:
    write_vacancy_to_db(item, db.vacancies)

print('Количество записей в коллекции:', db.vacancies.count_documents({}))

print_vacancies_greater_than(300_000, db.vacancies)


