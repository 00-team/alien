

import logging
from io import BytesIO
from tempfile import NamedTemporaryFile

import magic
from httpx import stream
from PIL import Image

from .utils import MediaError


def download_media(url: str) -> tuple[NamedTemporaryFile, str]:
    try:
        media = NamedTemporaryFile()
        with stream('GET', url) as response:
            # total = response.headers['Content-Length']
            # if total > 1024 * 1024 * 4:
            #     logging.warn(f'file too big: {total}')
            #     return None
            for chunk in response.iter_bytes():
                media.write(chunk)

        media.seek(0)
        mime_type = magic.from_buffer(media.read(2048), mime=True)

        logging.info(f'{mime_type=}')

        if mime_type not in ['image/gif', 'image/png', 'image/jpg']:
            logging.warn(f'invalid mime_type: {mime_type}')
            raise MediaError

        media.seek(0, 2)
        logging.info(f'file size: {(media.tell() / 1024):,}K')

        return media, mime_type
    except Exception as e:
        logging.exception(e)

    raise MediaError


def convert_media(file, mime_type: str) -> tuple[BytesIO, int]:
    file.seek(0, 0)
    media = BytesIO()

    try:
        image = Image.open(file)
        image.thumbnail(
            (512, 512),
            Image.Resampling.LANCZOS
        )
        image.save(media, format=image.format)
    except Exception as e:
        logging.exception(e)
        raise MediaError

    media.seek(0, 2)
    media_size = media.tell()
    logging.info(f'converted media size: {(media_size / 1024):,}K')

    return media, media_size
