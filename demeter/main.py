
import logging
import time

from nft import Artwork, Sold, eth_to_usd, get_artwork, get_sales
from shared import HOME_DIR, DbDict, format_duration, now

from twitter import tweet, upload_media

ART_DELAY = 10 * 60  # 10m
TWT_DELAY = 5 * 60  # 5m

db = DbDict(
    path=HOME_DIR / 'db.json',
    defaults={
        'T': [],  # Tweeted Already
        'last_date': now() - 24 * 3600,
    }
)


def art_tweet(sold: Sold, art: Artwork):
    media = upload_media(art.asset)
    asset_info = ''

    if art.mime_type in ['video/mp4']:
        asset_info = f'\n\n🎥 video {format_duration(art.duration)}'
    else:
        asset_type = 'gif' if art.mime_type == 'image/gif' else 'image'
        asset_info = f'\n\n📷 {asset_type}'

    tags = ' '.join([
        '#' + t.strip('#')
        for t in art.tags if ' ' not in t
    ][:3])
    if tags:
        tags += '\n'

    twt_id = tweet((
        f'🖼️ {art.name}\n\n'
        f'🎨 Artist {art.creator.in_twt}\n'
        f'🍾 Collector {art.owner.in_twt}\n'
        f'💰 Sold for {sold.price} #eth '
        f'(${eth_to_usd(sold.price)} USD) '
        'on the #foundation marketplace\n\n'
        f'{tags}'
        '🔗 Link👇👇👇'
        f'{asset_info}'
    ), media=media)

    if twt_id:
        tweet(
            ('https://foundation.app/collection/'
             f'{art.collection_slug}/{sold.token_id}'),
            reply=twt_id
        )


def main():
    last_twt = 0

    while True:
        last_date = db['last_date']
        before_tweets = now()

        logging.info(f'{before_tweets=}')

        for sold in get_sales(last_date, min_price=0.42):
            if sold.uid in db['T']:
                continue

            art = get_artwork(sold.token, sold.token_id)
            if art is None:
                continue

            time.sleep(max(TWT_DELAY - (now() - last_twt), 0))
            last_twt = now()

            art_tweet(sold, art)

            db['T'].append(sold.uid)
            db.save()

        time.sleep(max(ART_DELAY - (now() - before_tweets), 0))
        db['last_date'] = before_tweets


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.exception(e)
