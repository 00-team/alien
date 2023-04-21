import logging

from httpx import post
from pydantic import BaseModel

URL = 'https://hasura2.foundation.app/v1/graphql'


QUERY = '''
query ArtworkActivity($addr: String!, $token_id: numeric!) {
  artworks: artwork(
    where: {
      tokenId: { _eq: $token_id }
      contractAddress: { _ilike: $addr }
      deletedAt: { _is_null: true }
      hiddenAt: { _is_null: true }
    }
  ) {
    contractAddress
    id
    tags
    name
    lastSalePriceInETH

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


class User(BaseModel):
    name: str
    username: str
    public_key: str
    twitter: str = None

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

    @property
    def in_twt(self) -> str:
        if self.twitter:
            return '@' + self.twitter
        elif self.username:
            return self.username
        elif self.name:
            return self.name
        else:
            return self.public_key[:10] + '...'


class Artwork(BaseModel):
    name: str
    addr: str
    id: str
    tags: list[str]
    price: float

    asset: str
    duration: str | None
    mime_type: str

    collection_name: str
    collection_slug: str
    collection_maxt: int | None

    creator: User
    owner: User


def get_artwork(addr: str, token_id: int) -> Artwork:
    result = post(URL, json={
        'query': QUERY,
        'variables': {
            'addr': addr,
            'token_id': token_id
        }
    }, timeout=None)

    if result.status_code != 200:
        logging.error((
            f'error getting artwork {result.status_code}'
            f'\n\n{result.text}'
        ))
        return None

    arts = result.json()['data']['artworks']
    if not arts:
        return None

    a = arts[0]

    scheme = a['assetScheme']
    host = a['assetHost'].rstrip('/')
    path = a['assetPath'].lstrip('/')

    art = Artwork(
        name=a['name'],
        id=a['id'],
        addr=a['contractAddress'],
        tags=a['tags'],
        price=a['lastSalePriceInETH'],
        asset=f'{scheme}{host}/{path}',
        duration=a['duration'],
        mime_type=a['mimeType'],
        collection_name=a['collection']['name'],
        collection_slug=a['collection']['slug'],
        collection_maxt=a['collection']['maxTokenId'],
        creator=User.from_data(a['creator']),
        owner=User.from_data(a['owner']),
    )

    logging.info(f'art: {art.mime_type} {art.addr}')
    return art
