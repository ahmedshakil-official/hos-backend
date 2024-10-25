from django.core.management.base import NoArgsCommand

from ...helpers import get_secret_key


class Command(NoArgsCommand):
    help = "Prints a randomly generated string that can be used as a SECRET_KEY"

    def handle_noargs(self, **options):
        print get_secret_key()
