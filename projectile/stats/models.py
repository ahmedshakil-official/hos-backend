
from django.db import models

from common.models import CreatedAtUpdatedAtBaseModel

# create a model here that

class DailySaleSnapshot(CreatedAtUpdatedAtBaseModel):
    snapshot_date = models.DateField()
    stock_io = models.ForeignKey('pharmacy.StockIOLog', on_delete=models.CASCADE)
    purchase = models.ForeignKey('pharmacy.Purchase', on_delete=models.CASCADE) 
    invoice_group = models.ForeignKey('ecommerce.OrderInvoiceGroup', on_delete=models.CASCADE) 
    status = models.PositiveIntegerField()
    stock = models.ForeignKey('pharmacy.Stock', on_delete=models.CASCADE)
    product = models.ForeignKey('pharmacy.Product', on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    quantity = models.IntegerField()
    rate = models.DecimalField(max_digits=19, decimal_places=3)
    discount_rate = models.DecimalField(max_digits=19, decimal_places=3)
    sales_rate = models.DecimalField(max_digits=19, decimal_places=3)
    additional_discount_rate = models.DecimalField(max_digits=19, decimal_places=3)
    effective_sales_rate = models.DecimalField(max_digits=19, decimal_places=3)
    effective_sales_value = models.DecimalField(max_digits=19, decimal_places=3)
    order_additional_discount = models.DecimalField(max_digits=19, decimal_places=3)
    order_grand_total = models.DecimalField(max_digits=19, decimal_places=3)
    pharmacy_name = models.CharField(max_length=255)
    organization = models.ForeignKey('core.Organization', on_delete=models.CASCADE)
    delivery_thana = models.IntegerField(null=True, blank=True)
    address = models.CharField(max_length=200)
    employee = models.ForeignKey('core.PersonOrganization', on_delete=models.CASCADE)
    mobile = models.CharField(max_length=20)
    employee_first_name = models.CharField(max_length=255)
    employee_last_name = models.CharField(max_length=255)
    total_short = models.IntegerField(default=0)
    total_return = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Daily Sale Snapshot"
        index_together = ('snapshot_date', 'stock_io', 'organization', 'product', 'invoice_group')
        unique_together = ('snapshot_date', 'stock_io', 'organization', 'product', 'invoice_group')

    def __str__(self):
        return f"{self.pharmacy_name} / {self.order_grand_total}"


