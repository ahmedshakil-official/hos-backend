import logging

from dateutil.relativedelta import relativedelta
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

import pandas as pd

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = ''

    def handle(self, *args, **kwargs):
        # Calculate the date 6 months ago
        start_date = datetime.today() - relativedelta(months=3)
        # Current date
        end_date = datetime.today()

        # Generate all dates from 6 months ago to today
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')

        for date in date_range:
            date_ = date.strftime('%Y-%m-%d')
            try:
                # Call the convert_date command
                call_command('stats_create_daily_sale_snapshot', date_)
            except Exception as e:
                logger.exception(f'An error occurred on {date_}: {str(e)}')
                continue
