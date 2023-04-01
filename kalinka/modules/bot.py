
import json
import logging
import random
import time
from multiprocessing import Process

import httpx

from shared.database import load_json, read_db, save_json, setup_db
from shared.settings import BASE_DIR, BOT_DATA_PATH
from shared.tools import format_with_emojis

TOKEN_URL = 'https://api.twitter.com/2/oauth2/token'
SEARCH_URL = 'https://api.twitter.com/2/tweets/search/recent'

SEARCH_DELAY = 10 * 60
SHILL_DEALY = 30

BOT_SEC_PATH = BASE_DIR / 'bot.json'

BOT_INFO = load_json(BOT_SEC_PATH)
KEYS = load_json(BASE_DIR / 'keys.json')

DATA = setup_db({
    'total_search': 0,
    'shilled': [],
}, BOT_DATA_PATH)


def refresh_token():
    global BOT_INFO
    try:
        headers = {'Authorization': f'Basic {KEYS["BASIC_TOKEN"]}'}

        params = {
            'refresh_token': BOT_INFO['refresh_token'],
            'grant_type': 'refresh_token',
            'client_id': KEYS['CLIENT_ID']
        }

        response = httpx.post(TOKEN_URL, params=params, headers=headers)
        response = response.json()

        access_token = response.get('access_token')
        refresh_token = response.get('refresh_token')
        expires_in = response.get('expires_in')

        if access_token is None:
            logging.error('access_token is empty')
            logging.error(response)
            exit()

        data = {
            **BOT_INFO,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': int(time.time() + expires_in),
            'refresh_count': BOT_INFO.get('refresh_count', 0) + 1
        }

        save_json(data, BOT_SEC_PATH)

        BOT_INFO = data

    except Exception as e:
        logging.exception(e)
        exit()


def search(query: str):
    DATA['total_search'] += 1
    headers = {'Authorization': f'Bearer {BOT_INFO["access_token"]}'}
    params = {'query': query + ' -is:reply'}

    # 180 requests per 15-minute
    response = httpx.get(SEARCH_URL, params=params, headers=headers).json()
    tweets = [d['id'] for d in response.get('data', [])]

    logging.info(f'search len: {len(tweets)}')

    return tweets


# def retweet(hashtag, tweet_id):
#     url = f'https://api.twitter.com/2/users/{BOT_INFO["id"]}/retweets'
#
#     # 50 requests per 15-minute
#     response = httpx.post(url, headers=headers, json={'tweet_id': tweet_id})
#     logger.info(f'[retweet]: {tweet_id}')
#
#     if response.json().get('data', {}).get('retweeted'):
#         last_retweet(hashtag, tweet_id)
#     else:
#         logger.error(f'{response.status_code}:\n{response.text}')
#

def shill(tweets: list[str], text: str):
    headers = {'Authorization': f'Bearer {BOT_INFO["access_token"]}'}
    url = 'https://api.twitter.com/2/tweets'

    for i in tweets:
        try:
            if i in DATA['shilled']:
                continue

            response = httpx.post(url, headers=headers, json={
                'text': text,
                'reply': {
                    'in_reply_to_tweet_id': i
                }
            }).json()

            if response.get('data'):
                DATA['shilled'].append(i)
                logging.info(f'shilled {i}')

        except Exception as e:
            logging.exception(e)

        time.sleep(SHILL_DEALY)


def bot_loop():
    s = 0
    while True:
        time.sleep(1)

        try:
            s += 1
            if s < SEARCH_DELAY:
                continue
            else:
                s = 0

            db = read_db()
            if not db['active'] or not db['reply_tweets']:
                continue

            if time.time() + 30 > BOT_INFO['expires_in']:
                logging.info('refreshing ...')
                refresh_token()

            text = format_with_emojis(random.choice(db['reply_tweets']))

            tweet_ids = search(db['search'])
            shill(tweet_ids, text)

            save_json(DATA, BOT_DATA_PATH)
        except Exception as e:
            logging.exception(e)


def bot_start():
    Process(target=bot_loop).start()
