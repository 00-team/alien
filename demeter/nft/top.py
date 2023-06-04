
import logging

from .query import get_top_raw


def get_top(from_date: int) -> dict:
    data = {
        # byters
        'B': {},
        # creators
        'C': {},
    }

    events = get_top_raw(from_date)
    for idx, e in enumerate(events):
        price = float(e.get('amountInETH', 0))
        creator = e['nft']['creator']
        event_type = e['event']

        CID = None
        BID = None

        if creator:
            CID = creator.get('id')

        if event_type == 'Sold':
            BID = (e.get('auction', {}) .get('highestBid', {})
                   .get('bidder', {}).get('id'))

        elif event_type == 'OfferAccepted':
            BID = e.get('offer', {}).get('buyer', {}).get('id')

        elif event_type == 'PrivateSale':
            BID = e.get('privateSale', {}).get('buyer', {}).get('id')

        elif event_type == 'BuyPriceAccepted':
            BID = e.get('buyNow', {}).get('buyer', {}).get('id')

        if BID:
            if BID in data['B']:
                data['B'][BID]['price'] += price
                data['B'][BID]['total'] += 1
            else:
                data['B'][BID] = {
                    'price': price,
                    'total': 1
                }

        if CID:
            if CID in data['C']:
                data['C'][CID]['price'] += price
                data['C'][CID]['total'] += 1
            else:
                data['C'][CID] = {
                    'price': price,
                    'total': 1
                }

    def price_sort(item: dict):
        return item[1]['price']

    def total_sort(item: dict):
        return item[1]['total']

    creators = data['C'].items()
    buyers = data['B'].items()

    logging.info(f'{len(creators)=}')
    logging.info(f'{len(buyers)=}')

    return {
        'creators': {
            'total': sorted(creators, reverse=True, key=total_sort)[:5],
            'price': sorted(creators, reverse=True, key=price_sort)[:5]
        },
        'buyers': {
            'total': sorted(buyers, reverse=True, key=total_sort)[:5],
            'price': sorted(buyers, reverse=True, key=price_sort)[:5]
        }
    }


INDEX_EMOJI = {
    0: '🥇',
    1: '🥈',
    2: '🥉',
    3: '🎗',
    4: '🎗',
}


def get_top_tweet(data: dict):
    text = ''

    for idx, acc in enumerate([]):
        text += INDEX_EMOJI.get(idx, '-') + ' '
