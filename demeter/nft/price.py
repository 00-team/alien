

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


def eth_to_usd(eth: float) -> float:
    p = round(price_db['usd'] * eth, 2)

    if price_db['usd_ts'] + 10800 < now() and KEY['ETHERSCAN_TOKEN']:
        res = httpx.get(API_URL, params={
            'module': 'stats',
            'action': 'ethprice',
            'apikey': KEY['ETHERSCAN_TOKEN']
        })

        if res.status_code != 200:
            logging.error(f'Error getting eth price {res.status_code}')
            return p

        res = res.json()
        if res.get('status') != '1':
            return p

        res = res.get('result')
        if res is None:
            return p

        price_db.update({
            'btc': float(res['ethbtc']),
            'btc_ts': int(res['ethbtc_timestamp']),
            'usd': float(res['ethusd']),
            'usd_ts': int(res['ethusd_timestamp'])
        })
        return round(price_db['usd'] * eth, 2)

    return p
