
import time

from data import get_artwork, get_sales
from shared import HOME_DIR, DbDict

from twitter import tweet

ART_DELAY = 60 * 60  # 1h
TWT_DELAY = 30 * 60  # 30m

db = DbDict(
    path=HOME_DIR / 'db.json',
    defaults={
        'T': [],  # Tweeted Already
        'last_date': int(time.time()) - 24 * 3600
    }
)


def main():

    while True:
        lt = db['last_date']
        db['last_date'] = int(time.time())
        d = 0

        for sale in get_sales(lt, min_price=1):
            if sale.uid in db['T']:
                continue

            art = get_artwork(sale.token, sale.token_id)
            if art is None:
                continue

            print(sale.uid, sale.token, sale.token_id)

            time.sleep(TWT_DELAY)
            d += TWT_DELAY

        if d < ART_DELAY:
            time.sleep(ART_DELAY-d)

        d = 0


if __name__ == '__main__':
    main()
