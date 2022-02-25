from pprint import pprint
from datetime import date, timedelta

from lxml import html
import requests
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

urls = {
    'mail': 'https://news.mail.ru/',
    'lenta': 'https://lenta.ru/',
    'yandex': 'https://yandex.kz/news/'
}

headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/98.0.4758.82 Safari/537.36'}

client = MongoClient('localhost', 27017)
db = client['news']


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


def request_to_news_site(url, xpath_str):
    """
    Возвращает данные с сайта по xpath
    :param url: ссылка на сайт
    :param xpath_str: строка xpath
    :return:
    """
    try:
        response = requests.get(url, headers=headers)
        dom = html.fromstring(response.text)
        result = dom.xpath(xpath_str)

        return result
    except:
        print(f'Ошибка запроса к {url}')


def parse_lenta_data(data):
    """
    Разбирает данные с сайта https://lenta.ru/ и записывает их в БД
    :param data: данные для обработки
    :return:
    """
    for item in data:
        news = {}

        link = item.xpath('.//@href')[0]
        date_str = link.split('/')[2:5]

        news['_id'] = link.replace('/', '')
        news['source'] = 'https://lenta.ru'
        news['title'] = item.xpath(
            './/h3[contains(@class, "__title")]/text() | '
            './/span[contains(@class, "__title")]/text()')[0]
        news['link'] = news['source'] + link
        news['date'] = '/'.join(date_str)

        write_to_db(news, db.lenta)


def parse_yandex_data(data):
    """
    Разбирает данные с сайта https://yandex.kz/news/ и записывает их в БД
    :param data: данные для обработки
    :return:
    """
    for item in data:
        news = {}

        link = item.xpath('.//a[@class="mg-card__link"]/@href')[0]
        params = link.split('?')[1]

        title = item.xpath('.//a[@class="mg-card__link"]/text()')[0]

        news_time = item.xpath(
            './/span[@class="mg-card-source__time"]/text()')[0]
        news_date = date.today()
        if news_time.startswith('вчера'):
            news_date = date.today() - timedelta(days=1)

        news['_id'] = params.split('persistent_id=')[1].split('&')[0]
        news['link'] = link
        news['title'] = title.replace(u'\xa0', u' ')

        news['source'] = item.xpath(
            './/a[@class="mg-card__source-link"]/text()')[0]
        news['date'] = news_date.strftime("%Y/%m/%d")

        write_to_db(news, db.yandex)


if __name__ == '__main__':
    """ M A I L """  # не хватило времени
    # mail_news = request_to_news_site(
    #     urls['mail'],
    #     '//table[contains(@class, "daynews__inner")]//a[contains(@class, "js-topnews__item")]'
    # )

    print("*" * 35)

    """ L E N T A """
    lenta_data = request_to_news_site(urls['lenta'],
                                      '//a[contains(@class, "_topnews")]')
    parse_lenta_data(lenta_data)
    print('Количество записей с lenta.ru:', db.lenta.count_documents({}))

    print('Новости с lenta.ru:')
    for news in db.lenta.find({}):
        pprint(news)

    print("*" * 35)

    """ Y A N D E X """
    yandex_data = request_to_news_site(
        urls['yandex'],
        '//h1[@id="top-heading"]/following-sibling::node()/child::div'
    )
    parse_yandex_data(yandex_data)
    print('Количество записей с yandex:', db.yandex.count_documents({}))

    print('Новости с yandex:')
    for news in db.yandex.find({}):
        pprint(news)
