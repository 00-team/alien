
import json
import logging
import time

from httpx import post
from shared import HOME_DIR, DbDict

TOKEN_URL = 'https://api.twitter.com/2/oauth2/token'
TWEET_URL = 'https://api.twitter.com/2/tweets'


KEY = DbDict(path=HOME_DIR / 'keys.json', load=True)
BOT = DbDict(path=HOME_DIR / 'bot.json', load=True)


def refresh_token():
    try:
        headers = {'Authorization': f'Basic {KEY["BASIC_TOKEN"]}'}

        params = {
            'refresh_token': BOT['refresh_token'],
            'grant_type': 'refresh_token',
            'client_id': KEY['CLIENT_ID']
        }

        response = post(TOKEN_URL, params=params, headers=headers).json()

        access_token = response.get('access_token')
        refresh_token = response.get('refresh_token')
        expires_in = response.get('expires_in')

        if access_token is None:
            logging.error('access_token is empty')
            logging.error(json.dumps(response, indent=2))
            exit()

        BOT.update({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': int(time.time() + expires_in),
            'refresh_count': BOT.get('refresh_count', 0) + 1
        })

    except Exception as e:
        logging.exception(e)
        exit()


def tweet(text: str, reply: str = None) -> str:
    if time.time() + 30 > BOT['expires_in']:
        logging.info('refreshing the twitter token')
        refresh_token()

    headers = {'Authorization': f'Bearer {BOT["access_token"]}'}

    data = {'text': text}

    if reply:
        data['reply'] = {'in_reply_to_tweet_id': reply}

    response = post(TWEET_URL, headers=headers, json=data).json()
    return response['data']['id']
