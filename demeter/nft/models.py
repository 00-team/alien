from pydantic import BaseModel


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
    id: str
    tags: list[str]

    asset: str
    duration: float | None
    mime_type: str

    collection_name: str
    collection_slug: str
    collection_maxt: int | None

    creator: User
    owner: User
