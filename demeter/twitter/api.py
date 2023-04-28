
import base64
import hmac
import json
import logging
import time
from hashlib import sha1

from httpx import post
from shared import HOME_DIR, DbDict, now

from .media import convert_media, download_media
from .utils import MediaError, escape, random_string

TOKEN_URL = 'https://api.twitter.com/2/oauth2/token'
TWEET_URL = 'https://api.twitter.com/2/tweets'
MEDIA_URL = 'https://upload.twitter.com/1.1/media/upload.json'


KEY = DbDict(path=HOME_DIR / 'keys.json', load=True)
BOT = DbDict(path=HOME_DIR / 'bot.json', load=True)


media_db = DbDict(path=HOME_DIR / 'media.db.json')


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


def get_oauth(method, api_url, params={}):
    timestamp = str(now())
    nonce = timestamp + random_string(14)

    oauth_params = [
        ['oauth_consumer_key', KEY['API_KEY']],
        ['oauth_nonce', nonce],
        ['oauth_token', BOT['oauth_token']],
        ['oauth_signature_method', 'HMAC-SHA1'],
        ['oauth_timestamp', str(timestamp)],
        ['oauth_version', '1.0'],
    ]

    p = [
        f'{escape(str(k))}={escape(str(v))}'
        for k, v in [*oauth_params, *params.items()]
    ]
    p.sort()

    base_string = f'{method}&{escape(api_url)}&{escape("&".join(p))}'.encode()

    sign_key = (KEY['API_KEY_SECRET'] + '&' +
                BOT['oauth_token_secret']).encode()

    sout = base64.b64encode(
        hmac.new(sign_key, base_string, sha1).digest()
    ).decode()

    oauth_params.append(['oauth_signature', escape(sout)])

    return {
        'Authorization': 'OAuth ' + ', '.join(
            [f'{k}="{v}"' for k, v in oauth_params]
        )
    }


def upload_media(url: str, addr_token: str = None) -> str | None:
    try:
        if addr_token:
            mid = media_db.get(addr_token)
            if mid:
                return mid

        file, mime_type = download_media(url)
        media, media_size = convert_media(file, mime_type)

        # init upload
        params = {
            'command': 'INIT',
            'total_bytes': media_size,
            'media_type': mime_type,
        }

        result = post(
            MEDIA_URL,
            params=params,
            headers=get_oauth('POST', MEDIA_URL, params)
        )

        if result.status_code != 202:
            logging.error(f'media init error: {result.status_code}')
            logging.error(result.text)
            raise MediaError

        result = result.json()
        media_id = result['media_id_string']

        # append upload
        media.seek(0, 0)
        params = {
            'command': 'APPEND',
            'media_id': media_id,
            'segment_index': 0,
        }
        result = post(
            MEDIA_URL,
            params=params,
            files={'media': media},
            headers=get_oauth('POST', MEDIA_URL, params)
        )

        if result.status_code != 204:
            logging.error(f'media append error: {result.status_code}')
            logging.error(result.text)

            raise MediaError

        # upload finalize
        params = {
            'command': 'FINALIZE',
            'media_id': media_id,
        }
        result = post(
            MEDIA_URL,
            params=params,
            headers=get_oauth('POST', MEDIA_URL, params)
        )

        if result.status_code != 201:
            logging.error(f'media finalize error: {result.status_code}')
            logging.error(result.text)
            raise MediaError

        if media_id and addr_token:
            media_db[addr_token] = media_id

        return media_id
    except MediaError:
        return None


def tweet(text: str, media: str = None, reply: str = None) -> str | None:
    if time.time() + 30 > BOT['expires_in']:
        logging.info('refreshing the twitter token')
        refresh_token()

    headers = {'Authorization': f'Bearer {BOT["access_token"]}'}

    data = {'text': text}

    if reply:
        data['reply'] = {'in_reply_to_tweet_id': reply}

    if media:
        data['media'] = {'media_ids': [media]}

    response = post(TWEET_URL, headers=headers, json=data).json()
    twt_id = response.get('data', {}).get('id')
    if twt_id is None:
        logging.warn(json.dumps(response, indent=2))

    logging.info(f'tweeted: {twt_id} reply: {reply} media: {media}')

    return twt_id
