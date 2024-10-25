# locust -f locust/distributor.py --host $1
# locust -f locust/notification.py --host $1
# locust -f locust/promotion.py --host $1
locust -f locust/ecommerce_invoice_groups.py --host $1
# locust -f locust/notifications.py --host $1
# locust -f locust/lighthouse.py --host $1
