import json
import csv

import requests
from bs4 import BeautifulSoup

# https://hh.kz/search/vacancy?area=160&search_field=name&search_field=description&text=Python&clusters=true&ored_clusters=true&enable_snippets=true&page=1&hhtmFrom=vacancy_search_list
base_url = 'https://hh.kz'
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36'}
current_url = base_url + '/search/vacancy'

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
vacancy_list_csv = []


def convert_for_csv(data: dict) -> dict:
    converted_data = {}
    for k, v in data.items():
        if type(v) is dict:
            converted_data.update(**v)
            continue
        converted_data[k] = v
    return converted_data


def parse_vacancy_compensation(data: str) -> dict:
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

    return {'salary_from': data_from, 'salary_to': data_to, 'currency': data_currency}


while True:
    params['page'] = current_page
    response = requests.get(current_url, headers=headers, params=params)

    if response.ok:
        dom = BeautifulSoup(response.text, 'html.parser')

        if not num_pages or num_pages == 0:
            pager = dom.find('div', {'class': 'pager'})
            # num_pages = len(pager.findChildren(recursive=False)) - 1
            last_page_btn = pager.findChildren('span', recursive=False)[-1]
            num_pages = last_page_btn.find('span').get_text()
            num_pages = int(num_pages)

        vacancies = dom.select('div.vacancy-serp-item')

        for vacancy in vacancies:
            vacancy_data = {}

            vacancy_compensation = {'salary_from': None, 'salary_to': None, 'currency': None}
            vacancy_employer = None
            vacancy_city = None

            vacancy_title = vacancy.find('a', {'data-qa': 'vacancy-serp__vacancy-title'})

            vacancy_name = vacancy_title.text
            vacancy_link = vacancy_title['href']
            vacancy_link = vacancy_link.split('?')[0]  # как вариант

            vacancy_compensation_data = vacancy.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'})

            if vacancy_compensation_data:
                vacancy_compensation = parse_vacancy_compensation(vacancy_compensation_data.text)

            vacancy_employer_tag = vacancy.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'})
            if vacancy_employer_tag:
                vacancy_employer = vacancy_employer_tag.get_text(' ', strip=True)

            vacancy_city_div = vacancy.find('div', {'data-qa': 'vacancy-serp__vacancy-address'})
            vacancy_city = vacancy_city_div.get_text()

            vacancy_data['title'] = vacancy_name
            vacancy_data['link'] = vacancy_link
            vacancy_data['compensation'] = vacancy_compensation
            vacancy_data['site'] = base_url
            vacancy_data['employer'] = vacancy_employer
            vacancy_data['city'] = vacancy_city

            vacancy_list.append(vacancy_data)

            vacancy_list_csv.append(convert_for_csv(vacancy_data))

        current_page += 1
        if current_page > num_pages:
            break
    else:
        break


with open('hh_data.json', 'w', encoding='utf-8') as f:
    json_data = json.dumps(vacancy_list, indent=4, ensure_ascii=False)
    f.write(json_data)

with open('hh_data.csv', 'w', newline='', encoding='utf-8') as f:
    # headers = ('title', 'link', 'salary_from', 'salary_to', 'currency', 'site', 'employer', 'city')
    # Если очень хочется по русски
    headers = ('Вакансия', 'Ссылка', 'Зарплата_от', 'Зарплата_до', 'Валюта', 'Сайт_вакансии', 'Работодатель', 'Город')
    writer = csv.writer(f)
    writer.writerow(headers)

    for vacancy in vacancy_list_csv:
        writer.writerow(tuple(vacancy.values()))
