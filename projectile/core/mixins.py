import logging
from multiprocessing.pool import ThreadPool

from django.conf import settings
from django.shortcuts import get_object_or_404
from sorl.thumbnail import get_thumbnail

logger = logging.getLogger(__name__)


class UserThumbFieldMixin(object):
    """Adds a few thumb helpers for models with a single image field named image"""

    DEFAULT_IMAGE_PATH = {
        '64x64': f"{settings.FULL_STATIC_URL}images/placeholders/dude_64x64.png",
        '128x128': f"{settings.FULL_STATIC_URL}images/placeholders/dude_128x128.png",
        '256x256': f"{settings.FULL_STATIC_URL}images/placeholders/dude_256x256.png"
    }

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

    def get_thumb(self, size='64x64', quality=90):
        # Validate size to avoid unnecessary caching
        # chage to list because in python3 dict-keys can't iterating
        if size not in list(self.DEFAULT_IMAGE_PATH.keys()):
            size = '64x64'

        try:
            if not self.profile_image:
                return self.DEFAULT_IMAGE_PATH.get(size)
            else:
                path = self.profile_image
                thumb = get_thumbnail(
                    path, size, crop='center', quality=quality)
                return thumb.url
        except Exception as error:  # pylint: disable=broad-except
            # Returns default placeholder if error occurs
            logger.warning(error)
            logger.warning(
                'Could not get thumbnail for <User: {}> with <Image: {}>'.format(
                    self,
                    self.profile_image.url
                )
            )
            return self.DEFAULT_IMAGE_PATH.get(size)

    def get_thumb_small(self):
        thumb = self.get_thumb(size='64x64')
        return thumb

    def get_thumb_medium(self):
        return self.get_thumb(size='128x128')

    def get_thumb_large(self):
        return self.get_thumb(size='256x256')

    # create thumbnail for hero image.
    # default size 960x116
    def get_hero_image_thumbnail(self):
        if self.hero_image:
            thumb = get_thumbnail(
                self.hero_image, '960x116', crop='center', quality=99)
            return thumb
        return None


class OrganizationLogoFieldMixin(object):
    """Adds a few logo helpers for models with a single image field named logo"""

    DEFAULT_IMAGE_PATH = {
        '64x64': u"{}images/placeholders/logo_{}.png".format(settings.STATIC_URL, '64x64'),
        '128x128': u"{}images/placeholders/logo_{}.png".format(settings.STATIC_URL, '128x128'),
        '256x256': u"{}images/placeholders/logo_{}.png".format(settings.STATIC_URL, '256x256')
    }

    VALID_LITERAL_SIZES = [
        'small',
        'medium',
        'large',
    ]

    def create_logo(self):
        pool = ThreadPool(2)
        result = pool.map_async(
            lambda size: getattr(self, 'get_logo_{}'.format(size))(),
            self.VALID_LITERAL_SIZES
        )
        result.wait(10)
        pool.terminate()

    def get_logo(self, size='64x64', quality=90):
        # Validate size to avoid unnecessary caching
        # chage to list because in python3 dict-keys can't iterating
        if size not in list(self.DEFAULT_IMAGE_PATH.keys()):
            size = '64x64'

        try:
            if not self.logo:
                return self.DEFAULT_IMAGE_PATH.get(size)
            else:
                path = self.logo.path
                thumb = get_thumbnail(
                    path, size, crop='center', quality=quality)
                return thumb.url
        except Exception as error:  # pylint: disable=broad-except
            # Returns default placeholder if error occurs
            logger.warning(error)
            logger.warning(
                'Could not get logo for <Organization: {}> with <Image: {}>'.format(
                    self,
                    self.logo.path
                )
            )
            return self.DEFAULT_IMAGE_PATH.get(size)

    def get_logo_small(self):
        thumb = self.get_logo(size='64x64')
        return thumb

    def get_logo_medium(self):
        return self.get_logo(size='128x128')

    def get_logo_large(self):
        return self.get_logo(size='256x256')


class MultipleFieldLookupMixin:
    """
    Apply this mixin to any view or viewset to get multiple field filtering
    based on a `lookup_fields` attribute, instead of the default single field filtering.
    """
    def get_object(self):
        queryset = self.get_queryset()             # Get the base queryset
        queryset = self.filter_queryset(queryset)  # Apply any filter backends
        filter = {}
        for field in self.lookup_fields:
            if self.kwargs.get(field): # Ignore empty fields.
                filter[field] = self.kwargs[field]
        obj = get_object_or_404(queryset, **filter)  # Lookup the object
        self.check_object_permissions(self.request, obj)
        return obj
