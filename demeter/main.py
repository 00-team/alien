
import logging
import time

from nft import get_events
from shared import HOME_DIR, DbDict, now

from twitter import tweet, upload_media

ART_DELAY = 10 * 60  # 10m
TWT_DELAY = 40 * 60  # 5m

db = DbDict(
    path=HOME_DIR / 'db.json',
    defaults={
        'ET': [],  # Tweeted Already
        'last_date': now() - 24 * 3600,
        'last_tweet': 0
    }
)


def main():
    while True:
        last_date = db['last_date']
        before_tweets = now()

        for event in get_events(last_date, min_price=0.42):
            if event.uid in db['ET']:
                continue

            time.sleep(max(TWT_DELAY - (now() - db['last_tweet']), 0))
            db['last_tweet'] = now()

            tweet_text = event.tweet_message()

            if tweet_text:

                media = upload_media(event.art.asset, event.nft_id)
                twt_id = tweet(tweet_text, media=media)

                if twt_id:
                    tweet(
                        event.url,
                        reply=twt_id
                    )

            db['last_tweet'] = now()
            db['ET'].append(event.uid)
            db.save()

        time.sleep(max(ART_DELAY - (now() - before_tweets), 0))
        db['last_date'] = before_tweets


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.exception(e)
