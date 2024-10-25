from __future__ import division
from future.builtins import round


def post_save_order_delivery(sender, instance, created, **kwargs):
    if created:
        # Update amount related data for delivery instance
        instance.delivery.update_amount_related_data()

def post_save_delivery(sender, instance, created, **kwargs):
    pass
