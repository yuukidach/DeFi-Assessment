'''
This file is to collect data of finance risks.
'''
import requests
from bs4 import BeautifulSoup
import csv

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/87.0.4280.66 Safari/537.36 '
}


# get the link or data of the current url
def get_response(url):
    response = requests.get(url, headers=headers)
    return response.json()


# find the comments and save to file from aave
def get_comments_from_aave():
    ids = []
    titles = []
    f_aave = open('social/aave.csv', 'w', encoding='utf-8')
    csv_aave = csv.writer(f_aave)
    csv_aave.writerow(['title', 'comment', 'read', 'score', 'time'])

    # loop the topic of every category in aave
    for i in range(0, 100):
        url = 'https://governance.aave.com/latest.json?no_definitions=true&page=' + str(i)
        response = get_response(url)
        if response['topic_list']['topics']:
            for topic in response['topic_list']['topics']:
                titles.append(topic['title'])
                ids.append(topic['id'])
        else:
            break

    # loop each topic to get the comment, score, and reads
    for id in ids:
        detail_url = 'https://governance.aave.com/t/' + str(id) + '/posts.json'
        detail = get_response(detail_url)
        for post in detail['post_stream']['posts']:
            soup = BeautifulSoup(post['cooked'], 'lxml')
            comment = soup.getText()
            time = post['updated_at'][0:10]
            csv_aave.writerow([[titles[ids.index(id)]], comment, post['reads'], post['score'], time])

    f_aave.close()


# find the comments and save to file from compound
def get_comments_from_compound():
    ids = []
    titles = []
    f_compound = open('social/compound.csv', 'w', encoding='utf-8')
    csv_compound = csv.writer(f_compound)
    csv_compound.writerow(['title', 'comment', 'read', 'score', 'time'])

    # loop the topic of every category in compound
    for i in range(0, 100):
        url = 'https://www.comp.xyz/latest.json?no_definitions=true&page=' + str(i)
        response = get_response(url)
        if response['topic_list']['topics']:
            for topic in response['topic_list']['topics']:
                titles.append(topic['title'])
                ids.append(topic['id'])
        else:
            break

    # loop each topic to get the comment, score, and reads
    for id in ids:
        detail_url = 'https://www.comp.xyz/t/' + str(id) + '/posts.json'
        detail = get_response(detail_url)
        for post in detail['post_stream']['posts']:
            soup = BeautifulSoup(post['cooked'], 'lxml')
            comment = soup.getText()
            time = post['updated_at'][0:10]
            csv_compound.writerow([[titles[ids.index(id)]], comment, post['reads'], post['score'], time])

    f_compound.close()


# find the comments and save to file from truefi
def get_comments_from_truefi():
    ids = []
    titles = []
    f_truefi = open('social/truefi.csv', 'w', encoding='utf-8')
    csv_truefi = csv.writer(f_truefi)
    csv_truefi.writerow(['title', 'comment', 'read', 'score', 'time'])

    # loop the topic of every category in truefi
    for i in range(0, 100):
        url = 'https://forum.truefi.io/latest.json?no_definitions=true&page=' + str(i)
        response = get_response(url)
        if response['topic_list']['topics']:
            for topic in response['topic_list']['topics']:
                titles.append(topic['title'])
                ids.append(topic['id'])
        else:
            break

    # loop each topic to get the comment, score, and reads
    for id in ids:
        detail_url = 'https://forum.truefi.io/t/' + str(id) + '/posts.json'
        detail = get_response(detail_url)
        for post in detail['post_stream']['posts']:
            soup = BeautifulSoup(post['cooked'], 'lxml')
            comment = soup.getText()
            time = post['updated_at'][0:10]
            csv_truefi.writerow([[titles[ids.index(id)]], comment, post['reads'], post['score'], time])

    f_truefi.close()


# find the comments and save to file from cream
def get_comments_from_cream():
    ids = []
    titles = []
    f_cream = open('social/cream.csv', 'w', encoding='utf-8')
    csv_cream = csv.writer(f_cream)
    csv_cream.writerow(['title', 'comment', 'read', 'score', 'time'])

    # loop the topic of every category in cream
    for i in range(0, 100):
        url = 'https://forum.cream.finance/latest.json?no_definitions=true&page=' + str(i)
        response = get_response(url)
        if response['topic_list']['topics']:
            for topic in response['topic_list']['topics']:
                titles.append(topic['title'])
                ids.append(topic['id'])
        else:
            break

    # loop each topic to get the comment, score, and reads
    for id in ids:
        detail_url = 'https://forum.cream.finance/t/' + str(id) + '/posts.json'
        detail = get_response(detail_url)
        for post in detail['post_stream']['posts']:
            soup = BeautifulSoup(post['cooked'], 'lxml')
            comment = soup.getText()
            time = post['updated_at'][0:10]
            csv_cream.writerow([[titles[ids.index(id)]], comment, post['reads'], post['score'], time])

    f_cream.close()


# find the comments and save to file from alchemix
def get_comments_from_alchemix():
    ids = []
    titles = []
    f_alchemix = open('social/alchemix.csv', 'w', encoding='utf-8')
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
        detail_url = 'https://forum.alchemix.fi/public/api/discussions/' + str(id)
        detail = get_response(detail_url)
        for post in detail['included']:
            if post['type'] == 'posts' and post ['attributes']['contentType'] == 'comment':
                soup = BeautifulSoup(post['attributes']['contentHtml'], 'lxml')
                comment = soup.getText()
                csv_alchemix.writerow([[titles[ids.index(id)]], comment])

    f_alchemix.close()


# find the comments and save to file from dydx
def get_comments_from_dydx():
    ids = []
    titles = []
    f_dydx = open('social/dydx.csv', 'w', encoding='utf-8')
    csv_dydx = csv.writer(f_dydx)
    csv_dydx.writerow(['title', 'comment'])

    # loop the topic of every category in dydx
    response = get_response("https://forums.dydx.community/api/bulkThreads?chain=dydx")
    for thread in response['result']['threads']:
        titles.append(thread['title'])
        ids.append(thread['id'])

    # loop each topic to get the comment
    for id in ids:
        detail_url = 'https://forums.dydx.community/api/viewComments?chain=dydx&community=&root_id=discussion_' + str(id)
        detail = get_response(detail_url)
        for post in detail['result']:
            if post:
                comment = post['plaintext']
                csv_dydx.writerow([[titles[ids.index(id)]], comment])

    f_dydx.close()


if __name__ == '__main__':
    get_comments_from_aave()
    get_comments_from_compound()
    get_comments_from_cream()
    get_comments_from_truefi()
    get_comments_from_alchemix()
    get_comments_from_dydx()
