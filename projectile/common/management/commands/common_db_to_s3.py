# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

import os
import subprocess
import boto

from datetime import datetime, timedelta

from django.core.management.base import NoArgsCommand
from django.conf import settings

import dj_database_url


class Command(NoArgsCommand):
    help = "Temporary file that can be used to do temporary things"

    db_url = dj_database_url.parse(os.environ['DATABASE_URL'])

    user = db_url['USER']
    password = db_url['PASSWORD']
    name = db_url['NAME']
    host = db_url['HOST']
    port = db_url['PORT']

    aws_key = settings.AWS_ACCESS_KEY_ID
    aws_secret = settings.AWS_SECRET_ACCESS_KEY
    aws_bucket = os.environ['S3_DATABASE_BUCKET']

    directory = '/tmp/'
    filename_prefix = 'pgdump'

    conn = boto.connect_s3(
        os.environ['AWS_ACCESS_KEY_ID'], os.environ['AWS_SECRET_ACCESS_KEY'])
    bucket = conn.get_bucket(os.environ['S3_DATABASE_BUCKET'])

    # How many days should we keep the files?
    days_ago = datetime.now() - timedelta(days=7)
    hours_ago = datetime.now() - timedelta(hours=10)

    def handle_noargs(self, **options):
        # Generate file name
        path = self.generate_file_name()
        logger.info("Creating a pg_dump file in {} ...".format(path))
        path = self.create_dump(path)
        logger.info("Uploading file {} to S3 bucket ({}) ...".format(
            path, self.aws_bucket))
        self.upload_backup_file(path)
        logger.info('File upload was succesful...')
        self.remove_old_s3_backups()
        logger.info(
            "Removed old backups from bucket {}...".format(self.aws_bucket))
        self.remove_old_tmp_backups()

    def generate_file_name(self):
        # Returns the path and filename of the created file
        now = datetime.now()
        filename = "{}-{}-{}.bak".format(self.filename_prefix, now.date(
        ).strftime('%Y%m%d'), now.time().strftime('%H%M%S'))
        return os.path.realpath(os.path.join(self.directory, filename))

    def create_dump(self, path, big_dump=False):
        # 1. Creates a mysqldump file
        # 2. Returns the path of the created file
        try:
            command_string = "export PGPASSWORD={password}\npg_dump -Fc -U {user} -h {host} -p {port} {name} -f {path}"
            command = command_string.format(user=self.user,
                                            password=self.password,
                                            host=self.host,
                                            port=self.port,
                                            name=self.name,
                                            path=path)

            subprocess.call(command, shell=True)
            return path
        except Exception, e:
            # Send mail to alert admin
            raise e

    def upload_backup_file(self, path):
        from boto.s3.key import Key
        conn = boto.connect_s3(self.aws_key, self.aws_secret)
        bucket = conn.get_bucket(self.aws_bucket)
        k = Key(bucket)
        # Set key to filename only
        k.key = path.split('/')[-1]
        k.set_contents_from_filename(path)
        # k.get_contents_to_filename('bar.jpg')

    def remove_old_s3_backups(self):
        # Delete files older than a certain period from bucket.
        for key in self.bucket.list():
            timestamp = datetime.strptime(
                key.last_modified, '%Y-%m-%dT%H:%M:%S.%fZ')
            if timestamp < self.days_ago:
                logger.info("Deleting file {} from S3 bucket...".format(key))
                self.bucket.delete_key(key)

    def remove_old_tmp_backups(self):
        # Delete files from local folder
        for file in os.listdir(self.directory):
            if file.startswith(self.filename_prefix):
                path = "{}{}".format(self.directory, file)
                if os.path.exists(path):
                    t = os.path.getmtime(path)
                    timestamp = datetime.fromtimestamp(t)
                    if timestamp < self.hours_ago:
                        logger.info("Deleting file {} from ".format(path))
                        os.remove(path)

        logger.info(
            "Removed old backups from directory {}...".format(self.directory))
