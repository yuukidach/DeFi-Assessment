'''
This file is to collect data of finance risks.
'''
import requests
import csv
import logging
from bs4 import BeautifulSoup
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

headers = {
    'user-agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/87.0.4280.66 Safari/537.36 ')
}

FORUM_URLS = {
    'aave': 'https://governance.aave.com',
    'compound': 'https://www.comp.xyz',
    'truefi': 'https://www.comp.xyz',
    'cream': 'https://forum.cream.finance',
}


# get the link or data of the current url
def get_response(url):
    response = requests.get(url, headers=headers)
    return response.json()


# find the comments and save to file from alchemix
def save_comments_from_alchemix(target: Path):
    ids = []
    titles = []
    f_alchemix = open(target/'social/alchemix.csv', 'w', encoding='utf-8')
    csv_alchemix = csv.writer(f_alchemix)
    csv_alchemix.writerow(['title', 'comment'])

    # loop the topic of every category in alchemix
    response = get_response("https://forum.alchemix.fi/public/api/discussions")
    url = response['links']['next']
    for discussion in response['data']:
        titles.append(discussion['attributes']['title'])
        ids.append(discussion['attributes']['slug'])

    while url:
        response = get_response(url)
        for discussion in response['data']:
            titles.append(discussion['attributes']['title'])
            ids.append(discussion['attributes']['slug'])
        if len(response['links']) == 3:
            url = response['links']['next']
        else:
            break

    # loop each topic to get the comment
    for id in ids:
        detail_url = f'https://forum.alchemix.fi/public/api/discussions/{id}'
        detail = get_response(detail_url)
        for post in detail['included']:
            if post['type'] == 'posts' and \
               post['attributes']['contentType'] == 'comment':
                soup = BeautifulSoup(post['attributes']['contentHtml'], 'lxml')
                comment = soup.getText()
                csv_alchemix.writerow([[titles[ids.index(id)]], comment])

    f_alchemix.close()


# find the comments and save to file from dydx
def save_comments_from_dydx(target: Path):
    ids = []
    titles = []
    f_dydx = open(target/'social/dydx.csv', 'w', encoding='utf-8')
    csv_dydx = csv.writer(f_dydx)
    csv_dydx.writerow(['title', 'comment'])

    # loop the topic of every category in dydx
    response = get_response(
        "https://forums.dydx.community/api/bulkThreads?chain=dydx"
    )
    for thread in response['result']['threads']:
        titles.append(thread['title'])
        ids.append(thread['id'])

    # loop each topic to get the comment
    for id in ids:
        detail_url = ('https://forums.dydx.community/api/viewComments?chain='
                      'dydx&community=&root_id=discussion_' + str(id))
        detail = get_response(detail_url)
        for post in detail['result']:
            if post:
                comment = post['plaintext']
                csv_dydx.writerow([[titles[ids.index(id)]], comment])

    f_dydx.close()


def save_history_price(currency, target: Path):
    file_name = {'aave': 'aave', 'comp': 'compound', 'cream': 'cream',
                 'alcx': 'alchemix', 'dydx': 'dydx', 'tru': 'truefi'}
    limit = {'aave': '365', 'comp': '365', 'cream': '365',
             'alcx': '30', 'dydx': '30', 'tru': '30'}
    target = target / 'token_value'
    target.mkdir(parents=True, exist_ok=True)
    url = ("https://min-api.cryptocompare.com/data/v2/histoday?fsym="
           f'{currency}&tsym=USD&limit={limit[currency]}')
    response = get_response(url)
    file = open(target / f'{file_name[currency]}.csv', 'w', encoding='utf-8')
    csv_file = csv.writer(file)
    csv_file.writerow(['time', 'price', 'volume'])
    for cc in response['Data']['Data']:
        csv_file.writerow([cc['time'], cc['close'], cc['volumeto']])
    file.close()


def save_common_comment_csv(plat: str, target: Path):
    ids, titles = [], []
    target = target / 'social'
    target.mkdir(parents=True, exist_ok=True)
    with open(target / f'{plat}.csv', 'w', encoding='utf-8') as f:
        fcsv = csv.writer(f)
        fcsv.writerow(['title', 'comment', 'read', 'score', 'time'])

        for i in range(100):
            url = (f'{FORUM_URLS[plat]}/latest.json?no_definitions=true&page='
                   f'{i}')
            resp = get_response(url)
            if not resp['topic_list']['topics']:
                break
            for topic in resp['topic_list']['topics']:
                titles.append(topic['title'])
                ids.append(topic['id'])

        for id in ids:
            url = f'{FORUM_URLS[plat]}/t/{id}/posts.json'
            detail = get_response(url)
            for post in detail['post_stream']['posts']:
                soup = BeautifulSoup(post['cooked'], 'lxml')
                comment = soup.getText()
                time = post['updated_at'][:10]
                fcsv.writerow([
                    [titles[ids.index(id)]], comment, post['reads'],
                    post['score'], time
                ])


def create_finance_datasets(target: Path, force: bool):
    logger.info('Creating dataset for comments...')
    for plat in FORUM_URLS.keys():
        save_common_comment_csv(plat, target)
    save_comments_from_alchemix(target)
    save_comments_from_dydx(target)

    logger.info('Creating dataset for token values')
    save_history_price('aave')
    save_history_price('comp')
    save_history_price('cream')
    save_history_price('dydx')

    logger.info('Finance datasets are all created.')
