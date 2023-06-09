import base64
import hmac
import json
import logging
import time
from hashlib import sha1
from urllib.parse import quote

import httpx
from flask import Flask, redirect, render_template, request, session
from utils import BASE_DIR, error, merge_params, random_string, save_bot_token

from gshare import setup_logging

setup_logging(BASE_DIR)


AUTH2_URL = 'https://twitter.com/i/oauth2/authorize'
ACCESS_TOKEN_URL2 = 'https://api.twitter.com/2/oauth2/token'


with open(BASE_DIR / 'keys.json') as f:
    KEYS = json.load(f)


app = Flask(__name__, static_folder='static')
app.secret_key = KEYS['SECRET_KEY']


@app.get('/')
def index():
    return render_template('index.html')


@app.get('/update_bot/')
def update_bot():
    state = random_string()
    code_challenge = random_string()

    session['state'] = state
    session['code_challenge'] = code_challenge

    scopes = [
        'users.read', 'offline.access',
        'tweet.read', 'tweet.write'
    ]

    redirect_uri = request.root_url + 'callback/'

    params = {
        'response_type': 'code',
        'client_id': KEYS['CLIENT_ID'],
        'redirect_uri': redirect_uri,
        'scope': '+'.join(scopes),
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'plain',
    }

    url = merge_params(AUTH2_URL, params)

    return redirect(url)


@app.get('/callback/')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')

    session_state = session.get('state')
    code_challenge = session.get('code_challenge')

    if not session_state or state != session_state:
        return error('invalid state.')

    if not code_challenge:
        return error('invalid code challenge!')

    headers = {'Authorization': f'Basic {KEYS["BASIC_TOKEN"]}'}
    redirect_uri = request.root_url + 'callback/'

    params = {
        'grant_type': 'authorization_code',
        'client_id': KEYS['CLIENT_ID'],
        'code': code,
        'code_verifier': code_challenge,
        'redirect_uri': redirect_uri
    }

    response = httpx.post(ACCESS_TOKEN_URL2, params=params, headers=headers)

    if response.status_code != 200:
        logging.error(json.dumps(response.json(), indent=2))
        return error('error getting access token!')

    try:
        save_bot_token(response.json())
    except Exception:
        return error('Faild to Save the Info!')

    return redirect('/')


def escape(s: str) -> str:
    s = quote(s.encode('utf-8'), safe=b'~')

    if isinstance(s, bytes):
        s = s.decode('utf-8')

    return s


@app.get('/1')
def oauth1():
    try:
        api_url = 'https://api.twitter.com/oauth/request_token'
        cb = escape('http://136.243.198.57/cb1/')
        nonce = random_string(15)
        timestamp = int(time.time())

        oauth_params = [
            ['oauth_callback', cb],
            ['oauth_consumer_key', KEYS['API_KEY']],
            ['oauth_nonce', nonce],
            ['oauth_signature_method', 'HMAC-SHA1'],
            ['oauth_timestamp', str(timestamp)],
            ['oauth_version', '1.0'],
        ]

        p = [f'{k}={v}' for k, v in oauth_params]
        p.sort()

        base_string = f'POST&{escape(api_url)}&{escape("&".join(p))}'.encode()

        sign_key = (KEYS['API_KEY_SECRET'] + '&').encode()

        sout = base64.b64encode(
            hmac.new(sign_key, base_string, sha1).digest()
        ).decode()

        oauth_params.append(['oauth_signature', escape(sout)])

        headers = {
            'Authorization': 'OAuth ' + ', '.join(
                [f'{k}="{v}"' for k, v in oauth_params]
            )
        }

        res = httpx.post(api_url, headers=headers)
        if res.status_code != 200:
            return json.dumps({'error': 'status: ' + res.status_code})

        data = dict([i.split('=') for i in res.text.split('&')])
        return redirect((
            'https://api.twitter.com/oauth/authorize?'
            f'oauth_token={data["oauth_token"]}'
        ))

    except Exception as e:
        logging.exception(e)

    return '{"error":"GG"}'


@app.get('/cb1/')
def oauth1_cb():
    api_url = 'https://api.twitter.com/oauth/access_token'
    res = httpx.post(api_url, params={
        'oauth_verifier': request.args.get('oauth_verifier'),
        'oauth_token': request.args.get('oauth_token')
    })

    if res.status_code != 200:
        return json.dumps({'error': 'status: ' + res.status_code})

    data = dict([i.split('=') for i in res.text.split('&')])
    return json.dumps(data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
