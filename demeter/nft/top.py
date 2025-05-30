
import copy
import json
import logging

from shared.common import TWITTER_UN_TABLE

from .query import get_display_raw, get_top_raw

BOT_HASHTAG = '#FoundationSold'


def get_top_data(from_date: int) -> dict:
    data = {
        # byters
        'B': {},
        # creators
        'C': {},
    }

    events = get_top_raw(from_date)
    logging.info(f'events: {events}')
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

    logging.info(f'data: {data}')
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
            'total': copy.deepcopy(sorted(creators, reverse=True, key=total_sort)[:3]),
            'price': copy.deepcopy(sorted(creators, reverse=True, key=price_sort)[:3])
        },
        'buyers': {
            'total': copy.deepcopy(sorted(buyers, reverse=True, key=total_sort)[:3]),
            'price': copy.deepcopy(sorted(buyers, reverse=True, key=price_sort)[:3])
        }
    }

    for G in (
        top['creators']['total'],
        top['creators']['price'],
        top['buyers']['total'],
        top['buyers']['price']
    ):
        logging.info(f'G[0]: {G[0]}')
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
        user = get_display_raw(actor_pk=pk)
        top['users'][pk] = pk[:10] + '...'

        if not user or not user['actor']:
            continue

        name = user['actor'][0]['name']
        username = user['actor'][0]['username']
        twitter = user['actor'][0]['twitter']

        pk = pk.lower()
        display_name = pk[:10] + '...'
        # twt_pfx = '@' if idx < 3 else ''

        if twitter:
            display_name = twitter[0]['username']
        elif pk in TWITTER_UN_TABLE:
            display_name = TWITTER_UN_TABLE[pk]

        elif username:
            display_name = username
        elif name:
            display_name = name

        top['users'][pk] = '@' + display_name

    return top


INDEX_EMOJI = {
    0: '🥇 ',
    1: '🥈 ',
    2: '🥉 ',
    3: '🎗 ',
    4: '🎗 ',
}


def get_art(nft):
    art_data = get_display_raw(nft['pk'], nft['id'])
    if not art_data:
        return None

    art = art_data['art'][0]
    host = art['assetHost'].strip('/')
    path = art['assetPath'].strip('/')

    asset = f'{art["assetScheme"]}{host}/{path}'
    mime_type = art['mimeType']

    if not asset.endswith('.mp4') and mime_type in ['video/mp4']:
        asset += '/nft.mp4'

    return {
        'asset': asset,
        'id': nft['pk'] + '-' + str(nft['id']),
        'url': (
            f'https://foundation.app/collection/{art["collection"]["slug"]}'
            '?ref=0x46bc7892BEef62875511E35BdD8d1CB4407E7C53'
            # f'https://foundation.app/mint/eth/{nft["pk"]}/{nft["id"]}'
        )
    }


def get_top(from_date: int, date_name: str) -> tuple[str, dict]:
    data = get_top_data(from_date)
    logging.info(json.dumps(data, indent=2))

    G = data['creators']['total']
    nft = G[0][1]['top_nft']
    text = f'🏆 Top Creators of The {date_name}\n\n'

    for idx, user in enumerate(G):
        text += INDEX_EMOJI.get(idx, '- ')
        text += data['users'][user[0]]
        text += ' Sold ' + str(user[1]['total']) + ' Nfts.\n'

    text += '\n' + BOT_HASHTAG
    art = get_art(nft)
    yield text, art

    G = data['buyers']['total']
    nft = G[0][1]['top_nft']
    text = f'🏆 Top Collectors of The {date_name}\n\n'

    for idx, user in enumerate(G):
        text += INDEX_EMOJI.get(idx, '- ')
        text += data['users'][user[0]]
        text += ' Bought ' + str(user[1]['total']) + ' Nfts.\n'

    text += '\n' + BOT_HASHTAG
    art = get_art(nft)
    yield text, art

    G = data['creators']['price']
    nft = G[0][1]['top_nft']
    text = f'🏆 Top Creators of The {date_name}\n\n'

    for idx, user in enumerate(G):
        text += INDEX_EMOJI.get(idx, '- ')
        text += data['users'][user[0]]
        text += ' Sold ' + str(user[1]['price']) + ' Eth worth of Nfts.\n'

    text += '\n' + BOT_HASHTAG
    art = get_art(nft)
    yield text, art

    G = data['buyers']['price']
    nft = G[0][1]['top_nft']
    text = f'🏆 Top Collectors of The {date_name}\n\n'

    for idx, user in enumerate(G):
        text += INDEX_EMOJI.get(idx, '- ')
        text += data['users'][user[0]]
        text += ' Bought ' + str(user[1]['price']) + ' Eth worth of Nfts.\n'

    text += '\n' + BOT_HASHTAG
    art = get_art(nft)
    yield text, art
