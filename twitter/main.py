
import json
import random
import sys
import time
from itertools import cycle

import httpx
from utils import CONF, DATA_DIR, SECRETS_DIR, format_with_emojis, get_logger
from utils import last_retweet, load_json, read_shared_db, save_json

TOKEN_URL = 'https://api.twitter.com/2/oauth2/token'
SEARCH_URL = 'https://api.twitter.com/2/tweets/search/recent'

TWEET_DELAY = 5 * 60
SHILL_DEALY = 30

BOT_INFO = load_json(CONF['auth_path'])
KEYS = load_json(SECRETS_DIR / 'keys.json')

SDB = {
    'shilled': [],
    'total_search': 0
}
SDB_PATH = DATA_DIR / (BOT_INFO['username'] + '.sdb.json')

if SDB_PATH.is_file():
    SDB = load_json(SDB_PATH)


logger = get_logger(BOT_INFO['username'])


def refresh_token():
    global BOT_INFO

    try:
        headers = {'Authorization': f'Basic {KEYS["BASIC_TOKEN"]}'}

        params = {
            'refresh_token': BOT_INFO['refresh_token'],
            'grant_type': 'refresh_token',
            'client_id': KEYS['CLIENT_ID']
        }

        response = httpx.post(TOKEN_URL, params=params, headers=headers).json()

        access_token = response.get('access_token')
        refresh_token = response.get('refresh_token')
        expires_in = response.get('expires_in')

        if access_token is None:
            logger.error('access_token is empty')
            logger.error(json.dumps(response, indent=2))
            exit()

        data = {
            **BOT_INFO,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': int(time.time() + expires_in),
            'refresh_count': BOT_INFO.get('refresh_count', 0) + 1
        }

        filename = BOT_INFO['username']
        save_json(data, SECRETS_DIR / f'{filename}.json')

        BOT_INFO = data

    except Exception as e:
        logger.exception(e)
        exit()


def search(query: str) -> str | None:
    headers = {'Authorization': f'Bearer {BOT_INFO["access_token"]}'}
    params = {'query': query}

    # 180 requests per 15-minute
    response = httpx.get(SEARCH_URL, params=params, headers=headers).json()
    data = response.get('data', [])

    return data


def retweet(hashtag, tweet_id):
    last_rt, last_h_rt = last_retweet(BOT_INFO['username'], hashtag)

    if (last_h_rt == tweet_id) or (last_rt == tweet_id):
        return

    headers = {'Authorization': f'Bearer {BOT_INFO["access_token"]}'}

    url = f'https://api.twitter.com/2/users/{BOT_INFO["id"]}/retweets'

    # 50 requests per 15-minute
    response = httpx.post(url, headers=headers, json={'tweet_id': tweet_id})
    logger.info(f'[retweet]: {tweet_id}')

    if response.json().get('data', {}).get('retweeted'):
        last_retweet(BOT_INFO['username'], hashtag, tweet_id)
    else:
        logger.error(f'{response.status_code}:\n{response.text}')


def shill(tweets: list[str], text: str):
    headers = {'Authorization': f'Bearer {BOT_INFO["access_token"]}'}
    url = 'https://api.twitter.com/2/tweets'

    for i in tweets:
        try:
            if i in SDB['shilled']:
                continue

            response = httpx.post(url, headers=headers, json={
                'text': text,
                'reply': {
                    'in_reply_to_tweet_id': i
                }
            }).json()

            if response.get('data'):
                SDB['shilled'].append(i)
                logger.info(f'shilled {i}')

        except Exception as e:
            logger.exception(e)

        time.sleep(SHILL_DEALY)


def main(args: list[str]):
    htags = CONF['hashtags']

    for hashtag in cycle(htags + [12]):
        try:
            if time.time() + 30 > BOT_INFO['expires_in']:
                logger.info('refreshing...')
                refresh_token()

            if hashtag == 12:
                db = read_shared_db(BOT_INFO['username'])

                if not db['active'] or not db['reply_tweets']:
                    if not htags:
                        time.sleep(TWEET_DELAY)

                    # ignore the sleep
                    continue

                data = search(db['search'] + ' -is:reply')

                SDB['total_search'] += 1
                tweets = [d['id'] for d in data]
                logger.info(f'search len: {len(tweets)}')

                text = format_with_emojis(random.choice(db['reply_tweets']))
                shill(tweets, text)

                save_json(SDB, SDB_PATH)
            else:
                data = search(
                    f'#{hashtag} -from:{BOT_INFO["id"]} -is:retweet'
                )
                if len(data) > 0:
                    retweet(hashtag, data[0]['id'])

        except Exception as e:
            logger.exception(e)

        time.sleep(TWEET_DELAY)


if __name__ == '__main__':
    main(sys.argv)
