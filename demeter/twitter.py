
import base64
import hmac
import json
import logging
import random
import string
import time
from hashlib import sha1
from io import BytesIO
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
    s = quote(s.encode('utf-8'), safe=b'~')

    if isinstance(s, bytes):
        s = s.decode('utf-8')

    return s


def random_string(lenght=30) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choices(alphabet, k=lenght))


def get_oauth(method, api_url, params={}):
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

    p = [
        f'{escape(str(k))}={escape(str(v))}'
        for k, v in [*oauth_params, *params.items()]
    ]
    p.sort()
    logging.info(p)

    base_string = f'{method}&{escape(api_url)}&{escape("&".join(p))}'.encode()
    # base_string = f'{method}&{escape("&".join(p))}'.encode()

    sign_key = (KEY['API_KEY_SECRET'] + '&' +
                BOT['oauth_token_secret']).encode()

    sout = base64.b64encode(
        hmac.new(sign_key, base_string, sha1).digest()
    ).decode()

    oauth_params.append(['oauth_signature', escape(sout)])

    headers = {
        'Authorization': 'OAuth ' + ', '.join(
            [f'{k}="{v}"' for k, v in oauth_params]
        )
    }
    logging.info(json.dumps(headers, indent=2))
    return headers


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

    media_file = BytesIO()

    # convert
    try:
        image = Image.open(file)
        image.thumbnail(
            (512, 512),
            Image.Resampling.LANCZOS
        )
        image.save(media_file, format=image.format)
    except Exception as e:
        logging.exception(e)
        return None

    media_file.seek(0, 2)
    media_size = media_file.tell()
    logging.info(f'new file size: {(media_size / 1024):,}K')
    media_file.seek(0, 0)

    # file_size = 300224
    # mime_type = 'image/png'
    # new_file = BytesIO()

    # init upload
    params = {
        'command': 'INIT',
        'total_bytes': media_size,
        'media_type': mime_type,
    }

    result = post(
        api_url,
        params=params,
        headers=get_oauth('POST', api_url, params)
    )

    logging.info(f'init: {result.status_code}')

    if result.status_code >= 400:
        logging.error(f'media init error: {result.status_code}')
        logging.error(result.text)
        return None

    result = result.json()
    media_id = result['media_id_string']

    logging.info(f'[{media_id}] init\n' + json.dumps(result))

    # append upload
    params = {
        'command': 'APPEND',
        'media_id': media_id,
        'segment_index': 0,
    }
    result = post(
        api_url,
        params=params,
        files={'media': media_file},
        headers=get_oauth('POST', api_url, params)
    )

    logging.info(f'append: {result.status_code}')

    if result.status_code >= 400:
        logging.error(f'media append error: {result.status_code}')
        logging.error(result.text)

        return None

    # upload finalize
    params = {
        'command': 'FINALIZE',
        'media_id': media_id,
    }
    result = post(
        api_url,
        params=params,
        headers=get_oauth('POST', api_url, params)
    )

    logging.info(f'finalize: {result.status_code}')

    if result.status_code >= 400:
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
