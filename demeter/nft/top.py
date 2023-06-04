
from .query import get_top_raw


def get_top(from_date: int):
    data = {
        # byters
        'B': {},
        # creators
        'C': {},
    }

    events = get_top_raw(from_date)
    for e in events:
        price = float(e.get('amountInETH', 0))
        CID = e.get('nft', {}).get('creator', {}).get('id')
        BID = None
        event_type = e['event']

        if event_type == 'Sold':
            BID = (e.get('auction', {}) .get('highestBid', {})
                   .get('bidder', {}).get('id'))

    'Sold': Auction,
    'Bid': Auction,
    'OfferAccepted': Offer,
    'OfferMade': Offer,
    'PrivateSale': PrivateSale,
    'BuyPriceAccepted': BuyNow,
