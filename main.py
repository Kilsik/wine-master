import datetime
import collections
import argparse
import os

import pandas

from http.server import HTTPServer, SimpleHTTPRequestHandler
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape


def change_the_word(years):
    ''' Склонение "лет"/"год"/"года" '''

    if 5 <= (years % 100) <= 20:
        word = 'лет'
    elif (years % 10) == 1:
        word = 'год'
    elif 2 <= (years % 10) <= 4:
        word = 'года'
    else:
        word = 'лет'
    return f'{years} {word}'


def get_wines(file_name):
    ''' Из файла Excel получаем словарь с винами '''

    excel_wines = pandas.read_excel(file_name, na_filter=False)
    wines = excel_wines.to_dict('records')
    categories_header = excel_wines.columns[0]
    categories = excel_wines.agg(list,
        axis=0)[categories_header].drop_duplicates()
    return categories, wines, categories_header


def sort_by_categories(categories, wines, categories_header):
    ''' Сортируем вина по категориям '''

    wines_by_category = collections.defaultdict(list)
    for category in categories:
        for wine in wines:
            temporary = wines_by_category[category]
            if wine[categories_header] == category:
                temporary.append(wine)
    return wines_by_category


def replace_keys(categories, wines):
    ''' Меняем названия ключей словаря на латинские '''

    keys_replacements = ["category", "wine_name", "grape", "price", "img_url",
                        "special_offer"]
    wines_with_latin_keys = collections.defaultdict(list)
    for category in categories:
        for wine in wines[category]:
            temp_wine = dict(zip(keys_replacements, wine.values()))
            wines_with_latin_keys[category].append(temp_wine)
    return wines_with_latin_keys


if __name__ == '__main__':
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    parser = argparse.ArgumentParser(description='Сайт магазина вин')
    parser.add_argument('-f', '--file_path', help='Путь к файлу\
         с товарами')
    args = parser.parse_args()
    if args.file_path:
        file_path = args.file_path
    else:
        load_dotenv()
        file_path = os.getenv('FILE', 'assets/wine.xlsx')

    template = env.get_template('template.html')

    foundation = 1920
    years = datetime.datetime.now().year - foundation

    categories, wines, categories_header = get_wines(file_path)
    wines_by_category = sort_by_categories(categories, wines,
        categories_header)
    wines_with_latin_keys = replace_keys(categories, wines_by_category)

    rendered_page = template.render(
        winery_age=change_the_word(years),
        wines_by_category=wines_with_latin_keys,
        categories=categories,
    )

    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)

    server = HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestHandler)
    server.serve_forever()
