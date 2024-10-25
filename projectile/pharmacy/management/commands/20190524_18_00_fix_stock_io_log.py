import logging
from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.db.models.signals import pre_save, post_save


from common.helpers import (
    get_json_data_from_file,
)

from pharmacy.models import (
    Product,
    StockIOLog,
    Stock,
    OrganizationWiseDiscardedProduct
)
from pharmacy.signals import (
    post_save_product,
    pre_save_stock,
    pre_save_stock_io_log
)


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, **options):

        io_log_entries = get_json_data_from_file('tmp/io_log_list.json')
        stock_entries = get_json_data_from_file('tmp/stock_qty.json')
        product_entries = get_json_data_from_file('tmp/product_list_fix_product.json')

        post_save.disconnect(post_save_product, Product)
        pre_save.disconnect(pre_save_stock, Stock)
        pre_save.disconnect(pre_save_stock_io_log, StockIOLog)

        for item in tqdm(io_log_entries):
            io_log = StockIOLog.objects.get(id=item['id'])
            io_log.status = item['io_log_status']
            io_log.quantity = item['quantity']
            io_log.stock = Stock.objects.get(id=item['stock_id'])
            io_log.save(update_fields=['status', 'quantity', 'stock'])

        for stock in tqdm(stock_entries):
            product = Product.objects.get(id=stock['id'])
            stock_instance = Stock.objects.get(id=stock['stock_id'])

            product.status = stock['product_status']
            stock_instance.status = stock['stock_status']
            stock_instance.stock = stock['stock']
            product.save(update_fields=['status'])
            stock_instance.save(update_fields=['status', 'stock'])


        for item in tqdm(product_entries):
            product = Product.objects.get(id=item['product_id'])
            product.status = item['status']
            product.save(update_fields=['status'])



        discarded_products = OrganizationWiseDiscardedProduct.objects.filter(
            id__in=[
                75290, 75289, 75288, 75287, 75286, 75285, 75284, 75283, 75282, 75281, 75280,
                75279, 75278, 75277, 75269, 75268, 75267, 75266, 75265, 75264, 75263, 75262,
                75261, 75259, 75258, 75256, 75254, 75253, 75252, 75251, 75250, 75249, 75248,
                75247, 75246, 75245, 75244, 75243, 75242, 75241, 75240, 75239, 75235, 75232,
                75231, 75230, 75229, 75228, 75227, 75226, 75225, 75224, 75223, 75222, 75221,
                75220, 75219, 75218, 75216, 75215, 75214, 75212, 75211, 75210, 75209, 75208,
                75207, 75206, 75205, 75204, 75203, 75202, 75201, 75200, 75199, 75198, 75197,
                75196, 75195, 75194, 75193, 75192, 75191, 75190, 75189, 75188, 75187, 75186,
                75185, 75184, 75183, 75182, 75181, 75180, 75179, 75178, 75177, 75176, 75175,
                75174, 75173, 75171, 75170, 75169, 75168, 75167, 75166, 75165, 75164, 75163,
                75162, 75161, 75160, 75159, 75157, 75156
            ]
        )

        for discarded_product in tqdm(discarded_products):
            discarded_product.delete()
    
        post_save.connect(post_save_product, Product)
        pre_save.connect(pre_save_stock, Stock)
        pre_save.connect(pre_save_stock_io_log, StockIOLog)
