
import json
from datetime import datetime, timedelta

from httpx import Client
from pydantic import BaseModel

API_URL = 'https://hasura2.foundation.app/v1/graphql'

qlient = Client(base_url=API_URL, timeout=None)

TREND_Q = '''
query TrendingCollectors {
  items: trending_collector(
    order_by: [{oneDaySpent: desc}]
    limit: 20
    where: {
        user: { moderationStatus: { _eq: "ACTIVE" } }
        oneDaySpent: { _gte: 1 }
    }
  ) {
    total_bought: oneDayNumBought
    spent: oneDaySpent
    user {
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
  }
}
'''


ART_Q = '''
query UserArtworksCollected(
    $public_key: String!,
    $date: timestamp!,
    $min_price: numeric!,
    $limit: Int
) {
  artworks: artwork(
    where: {
      ownerPublicKey: { _eq: $public_key }
      publicKey: { _neq: $public_key }
      tokenId: { _is_null: false }
      deletedAt: { _is_null: true }
      hiddenAt: { _is_null: true }
      lastSalePriceInETH: { _is_null: false, _gte: $min_price }
      latestTxDate: { _gte: $date }
    }
    order_by: { latestTxDate: desc_nulls_last }
    limit: $limit
  ) {
    tags
    activeSalePriceInETH
    lastSalePriceInETH
    id
    latestTxDate
    name
    assetScheme
    assetHost
    assetPath
    duration
    mimeType
    tokenId
    status
    moderationStatus
    collection {
      slug
      name
    }
    creator: user {
      name
      publicKey
      username
      links
      twitter: socialVerifications(
        where: { isValid: { _eq: true }, service: { _eq: "TWITTER" } }
        limit: 1
      ) {
        username
      }
    }
  }
}
'''


class User(BaseModel):
    public_key: str
    twitter: str = None
    username: str
    name: str

    @classmethod
    def from_data(cls, data: dict):
        if data['twitter']:
            twitter = data['twitter'][0]['username']
        else:
            twitter = data['links'].get('twitter', {}).get('handle')

        return cls(
            twitter=twitter or None,
            username=data['username'] or '',
            name=data['name'] or '',
            public_key=data['publicKey']
        )


def main():
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()

    result = qlient.post('', json={'query': TREND_Q})
    if result.status_code != 200:
        print('Error ', result.status_code)
        return

    items = result.json()['data']['items']
    for i in items:
        buyer = User.from_data(i['user'])

        result = qlient.post('', json={
            'query': ART_Q,
            'variables': {
                'public_key': buyer.public_key,
                'limit': i['total_bought'],
                'date': yesterday,
                'min_price': 0.5
            }
        })

        if result.status_code != 200:
            print('Error Artworks', result.status_code)
            continue

        print(json.dumps(result.json(), indent=2))
        artworks = result.json()['data']['artworks']

        if not artworks:
            continue

        for a in artworks:
            seller = User.from_data(a['creator'])

            slug = a['collection']['slug']
            url = f'https://foundation.app/collection/{slug}/{a["tokenId"]}'
            price = a['lastSalePriceInETH']

            print(json.dumps(a, indent=2))
        break


if __name__ == '__main__':
    main()
