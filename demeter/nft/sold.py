
import logging
from datetime import datetime

from httpx import post
from pydantic import BaseModel

URL = 'https://api.thegraph.com/subgraphs/name/f8n/fnd'


QUERY = '''
query LatestSales($min_price: String!, $date: Int!) {
  buy_now: nftMarketBuyNows(
    where: {
        dateAccepted_gte: $date,
        amountInETH_gte: $min_price,
        nft_: {creator_not: null},
        buyer_not: null
    }
    orderBy: dateAccepted
    orderDirection: desc
  ) {
    dateAccepted
    nft {
      id
      tokenId
      creator {
        id
      }
    }
    buyer {
      id
    }
    amountInETH
  }
  auction: nftMarketAuctions(
    where: {
        dateFinalized_gte: $date,
        highestBid_: {amountInETH_gte: $min_price, bidder_not: null},
        nft_: {creator_not: null}
    }
    orderBy: dateFinalized
    orderDirection: asc
  ) {
    dateFinalized
    nft {
      id
      tokenId
      creator {
        id
      }
    }
    highestBid {
      amountInETH
      bidder {
        id
      }
    }
  }
}
'''


class Sold(BaseModel):
    uid: str
    datetime: datetime
    token: str
    token_id: int
    price: float
    owner: str
    creator: str


def get_sales(date, min_price=1) -> list[Sold]:
    result = post(URL, json={
        'query': QUERY,
        'variables': {
            'min_price': str(min_price),
            'date': int(date)
        }
    }, timeout=None)

    if result.status_code == 524:
        logging.error('server timeoit 524')
        return []

    if result.status_code != 200:
        logging.error((
            f'error getting sales {result.status_code}'
            f'\n\n{result.text}'
        ))
        return []

    data = result.json().get('data', {})

    buy_now = data.get('buy_now')
    auction = data.get('auction')

    if buy_now is None or auction is None:
        logging.error(f'{buy_now=} | {auction=}')
        return []

    if not buy_now and not auction:
        return []

    for a in auction:
        n = a['nft']
        h = a['highestBid']

        uid = a['dateFinalized'] + n['id'] + h['bidder']['id']

        sold = Sold(
            uid=uid,
            datetime=datetime.fromtimestamp(int(a['dateFinalized'])),
            token=n['id'].split('-')[0],
            token_id=n['tokenId'],
            price=h['amountInETH'],
            owner=h['bidder']['id'],
            creator=n['creator']['id']
        )

        logging.info(f'auction: {sold.token}/{sold.token_id} - {sold.price}')
        yield sold

    for b in buy_now:
        n = b['nft']
        uid = b['dateAccepted'] + n['id'] + b['buyer']['id']

        sold = Sold(
            uid=uid,
            datetime=datetime.fromtimestamp(int(b['dateAccepted'])),
            token=n['id'].split('-')[0],
            token_id=n['tokenId'],
            price=b['amountInETH'],
            owner=b['buyer']['id'],
            creator=n['creator']['id']
        )

        logging.info(f'buy_now: {sold.token}/{sold.token_id} - {sold.price}')
        yield sold
