
import base64
import hmac
import json
import logging
import random
import string
import time
from hashlib import sha1
from tempfile import NamedTemporaryFile
from urllib.parse import quote

import magic
from httpx import post, stream
from PIL import Image
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


def escape(s: str) -> str:
    return quote(s, safe='~')


def random_string(lenght=30) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choices(alphabet, k=lenght))


def get_oauth(method, api_url):
    nonce = random_string(15)
    timestamp = int(time.time())

    oauth_params = [
        ['oauth_consumer_key', KEY['API_KEY']],
        ['oauth_nonce', nonce],
        ['oauth_token', BOT['oauth_token']],
        ['oauth_signature_method', 'HMAC-SHA1'],
        ['oauth_timestamp', str(timestamp)],
        ['oauth_version', '1.0'],
    ]

    p = [f'{k}={v}' for k, v in oauth_params]
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


def upload_media(url: str) -> str | None:
    api_url = 'https://upload.twitter.com/1.1/media/upload.json'

    # download file
    file = NamedTemporaryFile()
    with stream('GET', url) as response:
        # total = response.headers['Content-Length']
        # if total > 1024 * 1024 * 4:
        #     logging.warn(f'file too big: {total}')
        #     return None
        for chunk in response.iter_bytes():
            file.write(chunk)

    # get mime_type
    file.seek(0)
    mime_type = magic.from_buffer(file.read(2048), mime=True)
    if mime_type not in ['image/gif', 'image/png', 'image/jpg']:
        logging.warn(f'invalid mime_type: {mime_type}')
        return None

    file.seek(0, 2)
    logging.info(f'file size: {(file.tell() / 1024):,}K')
    file.seek(0, 0)

    # convert
    try:
        image = Image.open(file)
        image.thumbnail(
            (512, 512),
            Image.Resampling.LANCZOS
        )
        image.save(file, format=image.format)
    except Exception as e:
        logging.exception(e)
        return None

    file.seek(0, 2)
    file_size = file.tell()
    logging.info(f'file size: {(file_size / 1024):,}K')
    file.seek(0, 0)

    # init upload
    result = post(
        api_url,
        params={
            'command': 'INIT',
            'total_bytes': file_size,
            'media_type': mime_type,
        },
        headers=get_oauth('POST', api_url)
    )
    if result.status_code != 200:
        logging.error(f'media init error: {result.status_code}')
        return None

    result.json()
    media_id = result['media_id_string']
    logging.info(f'[{media_id}] init\n' + json.dumps(result))

    # append upload

    result = post(
        api_url,
        params={
            'command': 'APPEND',
            'media_id': media_id,
            'segment_index': 0,
        },
        files={
            'media': file
        },
        headers=get_oauth('POST', api_url)
    )
    if result.status_code != 200:
        logging.error(f'media append error: {result.status_code}')
        logging.error(result.text)
        return None

    result = post(
        api_url,
        params={
            'command': 'FINALIZE',
            'media_id': media_id,
        },
        headers=get_oauth('POST', api_url)
    )
    if result.status_code != 200:
        logging.error(f'media finalize error: {result.status_code}')
        logging.error(result.text)
        return None

    logging.info('finalize\n'+json.dumps(result.json()))
    return media_id


def tweet(text: str, media: list[str] = None, reply: str = None) -> str | None:
    if time.time() + 30 > BOT['expires_in']:
        logging.info('refreshing the twitter token')
        refresh_token()

    headers = {'Authorization': f'Bearer {BOT["access_token"]}'}

    data = {'text': text}

    if reply:
        data['reply'] = {'in_reply_to_tweet_id': reply}

    if media and isinstance(media, list):
        data['media'] = {'media_ids': [str(i) for i in media]}

    response = post(TWEET_URL, headers=headers, json=data).json()
    twt_id = response.get('data', {}).get('id')
    if twt_id is None:
        logging.warn(json.dumps(response, indent=2))

    logging.info(f'tweeted: {twt_id} reply: {reply} media: {media}')

    return twt_id
