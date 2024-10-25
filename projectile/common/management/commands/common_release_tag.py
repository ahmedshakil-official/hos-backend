from django.core.management.base import BaseCommand

from ...helpers import ReleaseTagManager


class Command(BaseCommand):
    help = "Sets release tag in cache"

    def handle(self, **options):
        ReleaseTagManager.set()
