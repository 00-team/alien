

import logging
from io import BytesIO
from tempfile import NamedTemporaryFile

import magic
from httpx import stream
from PIL import Image

from .utils import MediaError


def download_media(url: str) -> tuple[NamedTemporaryFile, str]:
    try:
        logging.info(f'download: {url}')
        media = NamedTemporaryFile()
        with stream('GET', url) as response:
            total = int(response.headers.get('Content-Length', 0))
            if total > 100 * 1024 * 1024:
                logging.warn(f'file too big: {total}')
                raise MediaError

            for chunk in response.iter_bytes():
                media.write(chunk)

        media.seek(0)
        mime_type = magic.from_buffer(media.read(2048), mime=True)

        if mime_type not in [
            'image/gif', 'image/png',
            'image/jpg', 'image/jpeg',
            'video/mp4'
        ]:
            logging.warn(f'invalid mime_type: {mime_type}')
            raise MediaError

        return media, mime_type
    except MediaError:
        raise MediaError
    except Exception as e:
        logging.exception(e)

    raise MediaError


def convert_media(file, mime_type: str) -> tuple[BytesIO, int]:
    file_size = file.seek(0, 2)

    if mime_type == 'video/mp4':
        if file_size < 100 * 1024 * 1024:
            return file, file_size

        logging.warn(f'video file too big: {file_size:,}')
        raise MediaError

    if mime_type == 'image/gif' and file_size < 12 * 1024 * 1024:
        return file, file_size

    media = BytesIO()

    try:
        file.seek(0, 0)
        image = Image.open(file)
        image.thumbnail(
            (512, 512),
            Image.Resampling.LANCZOS
        )
        image.save(media, format=image.format)
    except Exception as e:
        logging.exception(e)
        raise MediaError

    media_size = media.seek(0, 2)
    if media_size > 4 * 1024 * 1024:
        logging.warn(
            f'img too big | before: {file_size:,} / after: {media_size:,}'
        )
        raise MediaError

    return media, media_size
