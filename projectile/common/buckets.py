from django.conf import settings
from django.core.files.storage import get_storage_class

from storages.backends.s3boto3 import S3Boto3Storage


class CachedS3Boto3Storage(S3Boto3Storage):
    """
    S3 storage backend that saves the files locally, too.
    """
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    custom_domain = settings._STATIC_URL[:-1]
    default_acl = 'public-read'

    def __init__(self, *args, **kwargs):
        super(CachedS3Boto3Storage, self).__init__(*args, **kwargs)
        self.local_storage = get_storage_class(
            "compressor.storage.CompressorFileStorage")()

    def save(self, name, content):
        self.local_storage._save(name, content)
        super(CachedS3Boto3Storage, self).save(name, self.local_storage._open(name))
        return name


class S3MediaStorage(S3Boto3Storage):
    bucket_name = settings.AWS_MEDIA_BUCKET_NAME
    custom_domain = settings._MEDIA_URL[:-1]
    default_acl = 'public-read'
    file_overwrite = False
