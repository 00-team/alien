import logging
import time
from datetime import datetime

from httpx import Response as _R
from httpx import post as _POST

_display_url = 'https://hasura2.foundation.app/v1/graphql'
_display_query = '''
query ArtworkActivity(
    $get_art: Boolean!, $get_actor: Boolean!,
    $addr: String, $token_id: numeric, $actor_pk: String
) {
  art: artwork(
    limit: 1,
    where: {
      tokenId: { _eq: $token_id }
      contractAddress: { _ilike: $addr }
      deletedAt: { _is_null: true }
      hiddenAt: { _is_null: true }
    }
  ) @include(if: $get_art) {
    contractAddress
    id
    tags
    name

    assetScheme
    assetHost
    assetPath
    duration
    mimeType

    collection {
      name
      slug
      maxTokenId
    }
    creator: user {
      ...UserFragment
    }
    owner {
      ...UserFragment
    }
  }

  actor: user(
    limit: 1,
    where: { publicKey: { _ilike: $actor_pk } }
  ) @include(if: $get_actor) {
    ...UserFragment
  }
}

fragment UserFragment on user {
  name
  username
  publicKey
  links
  twitter: socialVerifications(
    where: { isValid: { _eq: true }, service: { _eq: "TWITTER" } }
    limit: 1
  ) {
    username
  }
}
'''


_event_url = 'https://api.thegraph.com/subgraphs/name/f8n/fnd'
_event_query = '''
query Events($min_price: String!, $date: Int!){
  events: nftHistories(
    orderBy: date
    orderDirection: asc
    where: {
        amountInETH_gte: $min_price,
        event_in: [
            Sold, Bid,
            OfferAccepted, OfferMade,
            PrivateSale, BuyPriceAccepted
        ],
        date_gte: $date,
    }
  ) {
    amountInETH
    date
    event
    transactionHash

    nft {
      id
    }

    offer {
      buyer {
        id
      }
    }

    privateSale {
      buyer {
        id
      }
    }

    auction {
      highestBid {
        bidder {
          id
        }
        bidThisOutbid {
          amountInETH
          bidder {
            id
          }
        }
      }
    }

    buyNow {
      buyer {
        id
      }
    }

  }
}
'''


_top_query = '''
query TopEvents($date: Int!){
  events: nftHistories(
    orderBy: date
    orderDirection: asc
    where: {
        event_in: [
            Sold, OfferAccepted
            PrivateSale, BuyPriceAccepted
        ],
        date_gte: $date,
    }
  ) {
    amountInETH
    date
    event

    offer {
      buyer {
        id
      }
    }

    privateSale {
      buyer {
        id
      }
    }

    nft {
      id
      creator {
        id
      }
    }

    auction {
      highestBid {
        bidder {
          id
        }
      }
    }

    buyNow {
      buyer {
        id
      }
    }
  }
}
'''


def _graghql(url: str, query: str, variables: dict = {}) -> _R:
    result = _POST(url, json={
        'query': query,
        'variables': variables
    }, timeout=60)

    if result.status_code == 524:
        logging.error('server timeoit 524')

    elif result.status_code != 200:
        logging.error((
            f'error getting events {result.status_code}'
            f'\n\n{result.text}'
        ))

    return result


def get_events_raw(date, min_price) -> None | list[dict]:
    try:
        return _graghql(_event_url, _event_query, {
            'date': int(date),
            'min_price': str(min_price)
        }).json()['data']['events']
    except Exception as e:
        logging.error('error getting events.')
        logging.exception(e)


def get_top_raw(from_date: int) -> list[dict]:
    batchs = []

    try:
        date = int(from_date)
        n = 0
        while n < 100:
            events = _graghql(_event_url, _top_query, {
                'date': date,
            }).json()['data']['events']

            if not events:
                break

            batchs += events
            n += 1

            logging.info(
                f'iter: {n} - events: {len(events)} - batchs: {len(batchs)}'
            )
            logging.info(f'date: {str(datetime.fromtimestamp(date))}')

            date = int(events[-1]['date']) + 1

            time.sleep(0.5)

        return batchs
    except Exception as e:
        logging.error('error getting events.')
        logging.exception(e)

    return batchs


def get_display_raw(addr=None, tid=None, actor_pk=None) -> None | dict:
    if not ((addr and tid) or actor_pk):
        return None

    try:
        return _graghql(_display_url, _display_query, {
            'get_art': addr and (tid is not None),
            'get_actor': bool(actor_pk),
            'addr': str(addr),
            'token_id': int(tid),
            'actor_pk': str(actor_pk)
        }).json()['data']
    except Exception as e:
        logging.error('error getting display.')
        logging.exception(e)
