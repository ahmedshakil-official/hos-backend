#!/bin/bash

echo "--> rebuilding 'ElasticSearch index for Ecom Backend'..."
python projectile/manage.py search_index --rebuild --models pharmacy.Product -f $1
python projectile/manage.py search_index --rebuild --models clinic.OrganizationDepartment -f $1
python projectile/manage.py search_index --rebuild --models core.Department -f $1
python projectile/manage.py search_index --rebuild --models core.EmployeeDesignation -f $1
python projectile/manage.py search_index --rebuild --models core.Organization -f $1
python projectile/manage.py search_index --rebuild --models core.PersonOrganization -f $1
python projectile/manage.py search_index --rebuild --models core.Area -f $1
python projectile/manage.py search_index --rebuild --models pharmacy.ProductForm -f $1
python projectile/manage.py search_index --rebuild --models pharmacy.ProductGeneric -f $1
python projectile/manage.py search_index --rebuild --models pharmacy.ProductGroup -f $1
python projectile/manage.py search_index --rebuild --models pharmacy.ProductManufacturingCompany -f $1
python projectile/manage.py search_index --rebuild --models pharmacy.ProductSubgroup -f $1
python projectile/manage.py search_index --rebuild --models pharmacy.Purchase -f $1
python projectile/manage.py search_index --rebuild --models pharmacy.StorePoint -f $1
python projectile/manage.py search_index --rebuild --models pharmacy.Unit -f $1
python projectile/manage.py search_index --rebuild --models pharmacy.Stock -f $1
python projectile/manage.py search_index --rebuild --models ecommerce.OrderInvoiceGroup -f $1
echo "Done!"
