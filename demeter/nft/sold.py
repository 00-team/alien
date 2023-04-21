
import logging
from datetime import datetime

from httpx import post
from pydantic import BaseModel

URL = 'https://api.thegraph.com/subgraphs/name/f8n/fnd'


QUERY = '''
query LatestSales($min_price: Int!, $date: Int!) {
  items: nftTransfers(
    orderBy: dateTransferred
    orderDirection: desc
    first: 10
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


class Sale(BaseModel):
    uid: str
    datetime: datetime
    token: str
    token_id: int
    price: float
    owner: str
    creator: str


def get_sales(date, min_price=1) -> list[Sale]:
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

    for i in result.json()['data']['items']:
        n = i['nft']
        yield Sale(
            uid=i['id'],
            datetime=datetime.fromtimestamp(int(i['dateTransferred'])),
            token=n['id'].split('-')[0],
            token_id=n['tokenId'],
            price=n['lastSalePriceInETH'],
            owner=n['owner']['id'],
            creator=n['creator']['id']
        )
