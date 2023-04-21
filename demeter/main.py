
import logging
import time

import httpx
from nft import get_artwork, get_sales
from shared import HOME_DIR, DbDict, now

from twitter import tweet

ART_DELAY = 60 * 60  # 1h
TWT_DELAY = 10 * 60  # 10m
ESCN = 'https://api.etherscan.io/api'

db = DbDict(
    path=HOME_DIR / 'db.json',
    defaults={
        'T': [],  # Tweeted Already
        'last_date': now() - 24 * 3600,
        'eth_price': {
            'btc': 0.06793,
            'btc_ts': 1682085083,
            'usd': 1911.13,
            'usd_ts': 1682085081
        },
        'escn_token': None
    }
)


def eth_to_usd(eth: float) -> float:
    p = db['eth_price']['usd'] * eth

    if db['eth_price']['usd_ts'] + 10800 < now() and db['escn_token']:
        res = httpx.get(ESCN, params={
            'module': 'stats',
            'action': 'ethprice',
            'apikey': db['escn_token']
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

        db['eth_price'] = {
            'btc': float(res['ethbtc']),
            'btc_ts': int(res['ethbtc_timestamp']),
            'usd': float(res['ethusd']),
            'usd_ts': int(res['ethusd_timestamp'])
        }
        p = db['eth_price']['usd'] * eth

    return round(p, 2)


def main():

    while True:
        new_last_date = now()
        d = 0

        for sold in get_sales(db['last_date'], min_price=1):
            if sold.uid in db['T']:
                continue

            art = get_artwork(sold.token, sold.token_id)
            if art is None:
                continue

            twt_id = tweet((
                f'🖼️ {art.name}\n\n'
                f'🎨 Artist {art.creator.in_twt}\n'
                f'🍾 Collector {art.owner.in_twt}\n'
                f'💰 Sold for {sold.price} # eth '
                f'(${eth_to_usd(sold.price)} USD) '
                'on the #foundation marketplace'
                '\n\n🔗 Link👇👇👇'
            ))

            if twt_id:
                tweet(
                    ('https://foundation.app/collection/'
                     f'{art.collection_slug}/{sold.token_id}'),
                    twt_id
                )

            db['T'].append(sold.uid)
            db.save()

            time.sleep(TWT_DELAY)
            d += TWT_DELAY

        if d < ART_DELAY:
            time.sleep(ART_DELAY-d)

        d = 0
        db['last_date'] = new_last_date


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.exception(e)