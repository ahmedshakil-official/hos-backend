import logging

from datetime import datetime
import pandas as pd

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum, F

from pharmacy.models import Purchase, StockIOLog
from pharmacy.enums import OrderTrackingStatus
from ecommerce.models import ShortReturnItem
from ecommerce.enums import ShortReturnLogType
from common.enums import Status

from stats.models import DailySaleSnapshot

logger = logging.getLogger(__name__)

def get_stock_data(start_date, end_date):
    """
    Retrieve stock data within a specified date range.
    """
    purchases = Purchase.objects.filter(
        tentative_delivery_date__range=(start_date, end_date),
        distributor_order_type=2,
        purchase_type=4,
        status=13
    ).exclude(
        current_order_status__in=[
            OrderTrackingStatus.REJECTED,
            OrderTrackingStatus.CANCELLED,
        ]
    )

    stock_data = StockIOLog.objects.filter(
        purchase_id__in=purchases.values('id')
    ).values(
        'id', 'stock_id', 'stock__product_id', 'stock__product_full_name',
        'rate', 'quantity', 'discount_rate', 'purchase__id', 'purchase__organization_id',
        'purchase__organization__name', 'purchase__organization__delivery_thana',
        'purchase__organization__address', 'purchase__organization__primary_mobile',
        'purchase__responsible_employee__id', 'purchase__responsible_employee__first_name',
        'purchase__responsible_employee__last_name', 'purchase__additional_discount_rate',
        'purchase__additional_discount', 'purchase__invoice_group', 'purchase__current_order_status',
        'purchase__grand_total'
    )

    return pd.DataFrame(stock_data)

def rename_columns(dataframe, column_mapping):
    """
    Rename columns of a DataFrame based on a provided mapping.
    """
    dataframe.rename(columns=column_mapping, inplace=True)

def get_short_data(start_date, end_date, invoice_group_ids):
    """
    Retrieve short return data within a specified date range.
    """
    return pd.DataFrame(
        ShortReturnItem.objects.filter(
            date__range=(start_date, end_date),
            type=ShortReturnLogType.SHORT,
            status=Status.ACTIVE,
            short_return_log__invoice_group_id__in=invoice_group_ids
        ).values(
            'short_return_log__invoice_group_id', 'stock_io__stock_id'
        ).annotate(
            total_short=Sum(F('quantity'))
        )
    )

def get_product_return_data(invoice_group_ids):
    """
    Retrieve product return data for given invoice group IDs.
    """
    return pd.DataFrame(
        ShortReturnItem.objects.filter(
            type=ShortReturnLogType.RETURN,
            short_return_log__approved_at__isnull=False,
            status=Status.ACTIVE,
            short_return_log__invoice_group_id__in=invoice_group_ids
        ).values(
            'short_return_log__invoice_group_id', 'stock_io__stock_id'
        ).annotate(
            total_return=Sum(F('quantity'))
        )
    )


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('snapshot_date', type=str, help='Date in YYYY-MM-DD format')

    def handle(self, *args, **options):
        snapshot_date = options['snapshot_date']

        try:
            # Convert the string to a date object
            date_ = datetime.strptime(snapshot_date, '%Y-%m-%d').date()
            # Print the date object
            self.stdout.write(self.style.SUCCESS(f'Converted Date: {date_}'))
        except ValueError as e:
            raise CommandError('Date format must be YYYY-MM-DD') from e        

        start_date = date_
        end_date = date_

        logger.info(f"Creating daily sales snapshot records for date {start_date.strftime('%Y-%m-%d')}")
        try:
            # Retrieve and process stock data
            stock_out_data = get_stock_data(start_date, end_date)
            stock_column_mapping = {
                'id': 'stock_io_id',
                'stock_id': 'stock_id',
                'stock__product_id': 'product_id',
                'stock__product_full_name': 'product_name',
                'rate': 'rate',
                'quantity': 'quantity',
                'discount_rate': 'discount_rate',
                'purchase__id':'purchase_id',
                'purchase__organization_id': 'organization_id',
                'purchase__organization__name': 'pharmacy_name',
                'purchase__organization__delivery_thana': 'delivery_thana',
                'purchase__organization__address': 'address',
                'purchase__organization__primary_mobile': 'mobile',
                'purchase__responsible_employee__id': 'employee',
                'purchase__responsible_employee__first_name': 'employee_firs_name',
                'purchase__responsible_employee__last_name': 'employee_last_name',
                'purchase__additional_discount_rate': 'additional_discount_rate',
                'purchase__additional_discount': 'order_additional_discount',
                'purchase__invoice_group': 'invoice_group',
                'purchase__current_order_status' : 'status',
                'purchase__grand_total' : 'order_grand_total'
            }
            rename_columns(stock_out_data, stock_column_mapping)

            # Retrieve and process short return data
            invoice_group_ids = stock_out_data['invoice_group'].to_list()

            product_short_data = get_short_data(start_date, end_date, invoice_group_ids)
            
            short_return_column_mapping = {
                'short_return_log__invoice_group_id' : 'invoice_group',
                'stock_io__stock_id' : 'stock_id'
            }
            
            rename_columns(product_short_data, short_return_column_mapping)

            # Merge and process the data
            stock_out_data = stock_out_data.merge(product_short_data, on=['invoice_group', 'stock_id'], how='left')
            stock_out_data['total_short'].fillna(0, inplace=True)

            # Retrieve and process product return data
            product_return_data = get_product_return_data(invoice_group_ids)
            rename_columns(product_return_data, short_return_column_mapping)

            stock_out_data = stock_out_data.merge(product_return_data, on=['invoice_group', 'stock_id'], how='left')
            stock_out_data['total_return'].fillna(0, inplace=True)
            
            stock_out_data.loc[stock_out_data['status'] == 10, 'total_return'] = stock_out_data['quantity']
            stock_out_data['sales_rate'] = stock_out_data['rate'] - (stock_out_data['rate']/100)*stock_out_data['discount_rate']
            
            stock_out_data['effective_sales_rate'] = stock_out_data['sales_rate'] - (stock_out_data['sales_rate']/100)*stock_out_data['additional_discount_rate']    
            stock_out_data['effective_sales_value'] = stock_out_data['effective_sales_rate']*stock_out_data['quantity']
            
            new_column_order = [
                'stock_io_id', 'purchase_id', 'invoice_group', 'status', 'stock_id',
                'product_id', 'product_name', 'quantity', 'rate', 
                'discount_rate', 'sales_rate', 'additional_discount_rate', 'effective_sales_rate', 'effective_sales_value',  'order_additional_discount', 'order_grand_total',
                'pharmacy_name', 'organization_id', 'delivery_thana', 'address', 'mobile',
                'employee', 'employee_firs_name', 'employee_last_name',
                'total_short', 'total_return'
            ]

            # Reassign the DataFrame with the new column order
            stock_out_data = stock_out_data[new_column_order]

            # Fill NaN values with 0 for missing delivery_thana
            stock_out_data['delivery_thana'].fillna(0, inplace=True)

            rows = []
            for index, row in stock_out_data.iterrows():
                rows.append(
                    DailySaleSnapshot(
                        snapshot_date=start_date,
                        stock_io_id=row['stock_io_id'],
                        purchase_id=row['purchase_id'],
                        invoice_group_id=row['invoice_group'],
                        status=row['status'],
                        stock_id=row['stock_id'],
                        product_id=row['product_id'],
                        product_name=row['product_name'],
                        quantity=row['quantity'],
                        rate=row['rate'],
                        discount_rate=row['discount_rate'],
                        sales_rate=row['sales_rate'],
                        additional_discount_rate=row['additional_discount_rate'],
                        effective_sales_rate=row['effective_sales_rate'],
                        effective_sales_value=row['effective_sales_value'],
                        order_additional_discount=row['order_additional_discount'],
                        order_grand_total=row['order_grand_total'],
                        pharmacy_name=row['pharmacy_name'],
                        organization_id=row['organization_id'],
                        delivery_thana=row['delivery_thana'],
                        address=row['address'],
                        mobile=row['mobile'],
                        employee_id=row['employee'],
                        employee_first_name=row['employee_firs_name'],
                        employee_last_name=row['employee_last_name'],
                        total_short=row['total_short'],
                        total_return=row['total_return']
                    )
                )
            
            DailySaleSnapshot.objects.bulk_create(rows)
            logger.info(f"Created {len(rows)} daily sales snapshot records.")
        except Exception as e:
            logger.warn(f"Failed to create daily sales snapshot records for date {start_date.strftime('%Y-%m-%d')}.")
            logger.exception(e)

            
        
