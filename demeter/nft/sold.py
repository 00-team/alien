
import logging
from datetime import datetime

from httpx import post
from pydantic import BaseModel
from shared import now

URL = 'https://api.thegraph.com/subgraphs/name/f8n/fnd'


QUERY = '''
query LatestSales($min_price: Int!, $date: Int!) {
  items:nftMarketAuctions(
    where: {
        dateFinalized_gte: $date,
        highestBid_: {amountInETH_gte: $min_price}
    }
    orderBy: dateFinalized
    orderDirection: asc
  ) {
    dateFinalized
    auctionId

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
            'min_price': int(min_price),
            'date': int(date)
        }
    }, timeout=None)

    if result.status_code != 200:
        logging.error((
            f'error getting sales {result.status_code}'
            f'\n\n{result.text}'
        ))
        return []

    items = result.json().get('data', {}).get('items')
    if not items:
        logging.info(f'[sold] nothing new was found {now() - int(date)}')

    for i in items:
        n = i['nft']
        h = i['highestBid']

        sale = Sold(
            uid=i['auctionId'],
            datetime=datetime.fromtimestamp(int(i['dateFinalized'])),
            token=n['id'].split('-')[0],
            token_id=n['tokenId'],
            price=h['amountInETH'],
            owner=h['bidder']['id'],
            creator=n['creator']['id']
        )

        logging.info(f'sale: {sale.token}/{sale.token_id} - {sale.price}')
        yield sale


'''
query LatestSales($min_price: Int!, $date: Int!) {
  items: nftTransfers(
    orderBy: dateTransferred
    orderDirection: asc
    where: {
        nft_: {
            lastSalePriceInETH_gte: $min_price
        },
        dateTransferred_gt: $date
    }
  ) {
    id
    dateTransferred
    nft {
      id
      lastSalePriceInETH
      tokenId
      owner {
        id
      }
      creator {
        id
      }
    }
  }
}


'''
