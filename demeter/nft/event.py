
import logging
from abc import ABC, abstractmethod
from datetime import datetime

from shared import format_duration

from .models import Artwork, User
from .price import eth_usd_price
from .query import get_display_raw, get_events_raw


class BadEvent(Exception):
    pass


class Event(ABC):
    raw: dict

    price_eth: float
    date: datetime
    event: str
    usd_eth: float
    uid: str
    tx: str
    nft_id: str

    addr: str
    token_id: int
    art: Artwork

    actor_pk: str = None
    actor: User

    @abstractmethod
    def __init__(self, data: dict, usd_eth: float):

        if not self.actor_pk:
            raise BadEvent

        self.raw = data
        self.price_eth = float(data['amountInETH'])
        self.date = datetime.fromtimestamp(int(data['date']))
        self.event = data['event']
        self.uid = self.tx = data['transactionHash']

        self.nft_id = data['nft']['id']
        addr, tid = self.nft_id.split('-')
        self.addr = addr
        self.token_id = int(tid)

        self.usd_eth = usd_eth
        self.usd = round(self.price_eth * self.usd_eth, 2)

        try:
            data = get_display_raw(self.addr, self.token_id, self.actor_pk)
            art = data['art'][0]
            actor_data = data['actor'][0]
        except Exception as e:
            logging.exception(e)
            raise BadEvent

        self.actor = User.from_data(actor_data)

        host = art['assetHost'].strip('/')
        path = art['assetPath'].strip('/')

        asset = f'{art["assetScheme"]}{host}/{path}'
        mime_type = art['mimeType']

        if not asset.endswith('.mp4') and mime_type in ['video/mp4']:
            asset += '/nft.mp4'

        self.art = Artwork(
            name=art['name'],
            id=art['id'],
            tags=art['tags'],
            asset=asset,
            duration=art['duration'],
            mime_type=mime_type,
            collection_name=art['collection']['name'],
            collection_slug=art['collection']['slug'],
            collection_maxt=art['collection']['maxTokenId'],
            creator=User.from_data(art['creator']),
            owner=User.from_data(art['owner']),
        )

    @abstractmethod
    def tweet_message(self) -> str | None:
        return None

    @property
    def tags(self) -> str:
        tags = self.art.tags
        if not tags:
            return ''

        return ' '.join([
            '#' + t.strip('#')
            for t in self.art.tags if ' ' not in t
        ][:3])

    @property
    def asset_info(self) -> str:
        mime_type = self.art.mime_type

        if mime_type == 'video/mp4':
            return f'🎥 video {format_duration(self.art.duration)}'
        elif mime_type == 'image/gif':
            return '🎞 gif'
        else:
            return '📷 image'

    @property
    def url(self):
        return (
            'https://foundation.app/collection/'
            f'{self.art.collection_slug}/{self.token_id}'
        )


class Auction(Event):
    ob_user: User = None
    ob_price: float = None

    def __init__(self, data: dict, *args, **kwargs):
        a = data['auction']
        self.actor_pk = a['highestBid']['bidder']['id']
        ob = a.get('bidThisOutbid', None)

        if ob:
            obd = get_display_raw(None, None, ob['bidder']['id']) or {}
            obda = obd.get('actor')

            if obda:
                self.ob_price = float(ob['amountInETH'])
                self.ob_user = User.from_data(obda)

        super().__init__(data, *args, **kwargs)

    def sold_message(self):

        return (
            f'🖼️ {self.art.name}\n\n'
            f'🎨 Artist {self.art.creator.in_twt}\n'
            f'🍾 Collector {self.art.owner.in_twt}\n'
            f'💰 Sold for {self.price_eth} #eth (${self.usd} USD) '
            'on the #foundation marketplace\n\n'
            f'{self.tags}\n'
            '🔗 Link👇👇👇\n\n'
            f'{self.asset_info}'
        )

    def bid_message(self):
        ob = ''

        if self.ob_user:
            ob = f'Old bid {self.price_eth} eth by {self.ob_user.in_twt}\n'

        return (
            '💠 Auction\n\n'
            f'🖼️ {self.art.name}\n'
            f'New bid {self.price_eth} #eth '
            f'(${self.usd} USD) by {self.actor.in_twt}\n{ob}'
            f'🎨 Artist {self.art.creator.in_twt}\n'
            'On #foundation\n\n'
            '→ 💎 Did you have a higher offer?'
            f'{self.tags}\n'
            '🔗 Link👇👇👇\n\n'
            f'{self.asset_info}'
        )

    def tweet_message(self):
        if self.event == 'Sold':
            return self.sold_message()
        else:
            return self.bid_message()


class BuyNow(Event):
    def __init__(self, data, *args, **kwargs):
        self.actor_pk = data['buyNow']['buyer']['id']
        super().__init__(data, *args, **kwargs)

    def tweet_message(self):
        return (
            f'🖼️ {self.art.name}\n\n'
            f'🎨 Artist {self.art.creator.in_twt}\n'
            f'🍾 Collector {self.art.owner.in_twt}\n'
            f'💰 Sold for {self.price_eth} #eth (${self.usd} USD) '
            'on the #foundation marketplace\n\n'
            f'{self.tags}\n'
            '🔗 Link👇👇👇\n\n'
            f'{self.asset_info}'
        )


class Offer(Event):
    def __init__(self, data, *args, **kwargs):
        self.actor_pk = data['offer']['buyer']['id']
        super().__init__(data, *args, **kwargs)

    def offer_made_message(self):
        return (
            f'🔔 New Offer by {self.actor.in_twt}'
            f'for 💰 {self.price_eth} #eth (${self.usd} USD) \n'
            f'🖼️ {self.art.name}\n\n'
            f'🎨 Artist {self.art.creator.in_twt}\n'
            'on the #foundation marketplace\n\n'
            f'{self.tags}\n'
            '🔗 Link👇👇👇\n\n'
            f'{self.asset_info}'
        )

    def offer_accepted_message(self):
        return (
            f'🖼️ {self.art.name}\n\n'
            f'🎨 Artist {self.art.creator.in_twt}\n'
            f'🍾 Collector {self.art.owner.in_twt}\n'
            f'💰 Sold for {self.price_eth} #eth (${self.usd} USD) '
            'on the #foundation marketplace\n\n'
            f'{self.tags}\n'
            '🔗 Link👇👇👇\n\n'
            f'{self.asset_info}'
        )

    def tweet_message(self):
        if self.event == 'OfferMade':
            return self.offer_made_message()
        else:
            return self.offer_accepted_message()


class PrivateSale(Event):
    def __init__(self, data, *args, **kwargs):
        self.actor_pk = data['privateSale']['buyer']['id']
        super().__init__(data, *args, **kwargs)

    def tweet_message(self):
        usd = round(self.price_eth * self.usd_eth, 2)

        return (
            f'🖼️ {self.art.name}\n\n'
            f'🎨 Artist {self.art.creator.in_twt}\n'
            f'🍾 Collector {self.art.owner.in_twt}\n'
            f'💰 Private Saled for {self.price_eth} #eth (${usd} USD) '
            'on the #foundation marketplace\n\n'
            f'{self.tags}\n'
            '🔗 Link👇👇👇\n\n'
            f'{self.asset_info}'
        )


event_table = {
    'Sold': Auction,
    'Bid': Auction,
    'OfferAccepted': Offer,
    'OfferMade': Offer,
    'PrivateSale': PrivateSale,
    'BuyPriceAccepted': BuyNow,
}


def get_events(date, min_price) -> list[Event]:
    events = get_events_raw(date, min_price)
    if not events:
        return []

    eth_price = eth_usd_price()

    for a in events:
        try:
            e = event_table[a['event']](a, eth_price)
            logging.info(f'{e.event}: {e.addr}/{e.token_id} - {e.price_eth}')
            yield e
        except BadEvent:
            continue
