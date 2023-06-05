
import json
import logging
import time

from .query import get_display_raw, get_top_raw


def get_top_data(from_date: int) -> dict:
    data = {
        # byters
        'B': {},
        # creators
        'C': {},
    }

    events = get_top_raw(from_date)
    for idx, e in enumerate(events):
        price = float(e.get('amountInETH', 0))
        nft_id = e['nft']['id'] + ':' + e.get('amountInETH')
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
                data['B'][BID]['nfts'].add(nft_id)
            else:
                data['B'][BID] = {
                    'price': price,
                    'total': 1,
                    'nfts': {nft_id}
                }

        if CID:
            if CID in data['C']:
                data['C'][CID]['price'] += price
                data['C'][CID]['total'] += 1
                data['C'][CID]['nfts'].add(nft_id)
            else:
                data['C'][CID] = {
                    'price': price,
                    'total': 1,
                    'nfts': {nft_id}
                }

    def price_sort(item: dict):
        return item[1]['price']

    def total_sort(item: dict):
        return item[1]['total']

    def nft_sort(item: str):
        return float(item.split(':')[-1])

    creators = data['C'].items()
    buyers = data['B'].items()

    logging.info(f'{len(creators)=}')
    logging.info(f'{len(buyers)=}')

    top = {
        'creators': {
            'total': sorted(creators, reverse=True, key=total_sort)[:5],
            'price': sorted(creators, reverse=True, key=price_sort)[:5]
        },
        'buyers': {
            'total': sorted(buyers, reverse=True, key=total_sort)[:5],
            'price': sorted(buyers, reverse=True, key=price_sort)[:5]
        }
    }

    for G in (
        top['creators']['total'],
        top['creators']['price'],
        top['buyers']['total'],
        top['buyers']['price']
    ):
        top_nft = max(list(G[0][1].pop('nfts')), key=nft_sort)
        logging.info(f'top nft: {top_nft}')

        nft_id, nft_price = top_nft.split(':')
        nft_pk, token_id = nft_id.split('-')

        G[0][1]['top_nft'] = {
            'pk': nft_pk,
            'id': int(token_id),
            'price': float(nft_price)
        }

        for u in G[1:]:
            u[1].pop('nfts', None)

    all_users = set()
    for user in (
        top['creators']['total'] +
        top['creators']['price'] +
        top['buyers']['total'] +
        top['buyers']['price']
    ):
        all_users.add(user[0])

    top['users'] = {}

    for idx, pk in enumerate(all_users):
        logging.info(f'getting user info: {idx}')
        time.sleep(0.3)
        user = get_display_raw(actor_pk=pk)

        top['users'][pk] = {
            'pk': pk
        }

        if user is None:
            continue

        top['users'][pk]['name'] = user['actor']['name']
        top['users'][pk]['username'] = user['actor']['username']
        top['users'][pk]['twitter'] = user['actor']['twitter']

    return top


INDEX_EMOJI = {
    0: '🥇',
    1: '🥈',
    2: '🥉',
    3: '🎗',
    4: '🎗',
}


def get_top(from_date: int):
    data = get_top(from_date)
    logging.info(json.dumps(data, indent=2))
    text = ''

    for idx, acc in enumerate([]):
        text += INDEX_EMOJI.get(idx, '-') + ' '
