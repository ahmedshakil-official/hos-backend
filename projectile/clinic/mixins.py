import logging
from multiprocessing.pool import ThreadPool
from sorl.thumbnail import get_thumbnail

logger = logging.getLogger(__name__)


class ImageThumbFieldMixin(object):
    """Adds a few thumb helpers for models with a single image field named image"""

    VALID_LITERAL_SIZES = [
        'small',
        'medium',
        'large',
    ]

    def create_thumbnails(self):
        pool = ThreadPool(2)
        result = pool.map_async(
            lambda size: getattr(self, 'get_thumb_{}'.format(size))(),
            self.VALID_LITERAL_SIZES
        )
        result.wait(10)
        pool.terminate()

    def get_thumb(self, size='654x350', quality=90):
        try:
            path = self.image.path
            thumb = get_thumbnail(path, size, crop='center', quality=quality)
            return thumb

        except Exception as error:  # pylint: disable=broad-except
            logger.warning(error)
            logger.warning('Could not get thumbnail for <Image: {}>'.format(self.image.path))

    def get_thumb_small(self):
        return self.get_thumb(size='320x320')

    def get_thumb_medium(self):
        return self.get_thumb(size='654x350')

    def get_thumb_large(self):
        return self.get_thumb(size='980x400')
