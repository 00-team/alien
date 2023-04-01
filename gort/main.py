import json

import httpx
from flask import Flask, redirect, render_template, request, session
from utils import BASE_DIR, error, get_logger, merge_params, random_string
from utils import save_bot_token

logger = get_logger('main')


AUTH_BASE_URL = 'https://twitter.com/i/oauth2/authorize'
ACCESS_TOKEN_URL = 'https://api.twitter.com/2/oauth2/token'


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

    url = merge_params(AUTH_BASE_URL, params)

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

    response = httpx.post(ACCESS_TOKEN_URL, params=params, headers=headers)

    if response.status_code != 200:
        logger.error(json.dumps(response.json(), indent=2))
        return error('error getting access token!')

    try:
        save_bot_token(response.json())
    except Exception:
        return error('Faild to Save the Info!')

    return redirect('/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
