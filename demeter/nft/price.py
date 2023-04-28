

import logging

import httpx
from shared import HOME_DIR, DbDict, now

from twitter.api import KEY

API_URL = 'https://api.etherscan.io/api'

price_db = DbDict(
    path=HOME_DIR / 'price.db.json',
    defaults={
        'btc': 0.06,
        'btc_ts': 1682085083,
        'usd': 2000,
        'usd_ts': 1682085081,
    }
)


def update_price():
    if price_db['usd_ts'] + 10800 > now() and KEY['ETHERSCAN_TOKEN']:
        return

    try:
        res = httpx.get(API_URL, params={
            'module': 'stats',
            'action': 'ethprice',
            'apikey': KEY['ETHERSCAN_TOKEN']
        }).json()['result']

        price_db.update({
            'btc': float(res['ethbtc']),
            'btc_ts': int(res['ethbtc_timestamp']),
            'usd': float(res['ethusd']),
            'usd_ts': int(res['ethusd_timestamp'])
        })
    except Exception as e:
        logging.error('Error getting eth price')
        logging.exception(e)


def eth_to_usd(eth: float) -> float:
    update_price()
    return round(price_db['usd'] * eth, 2)


def eth_usd_price() -> float:
    update_price()
    return price_db['usd']
