#!/bin/bash

: '
A new bash script against a python script has been added for handling elastic search command,
The script will fully support all django_elasticsearch_dsl command,
Additionally, it can perform index rebuild, populate, create, delete index of a custom model list.
./search_index.sh --rebuild -f --single --custom_list command will rebuild and ./search_index.sh --populate -f --single --custom_list command all indices one by one from the defined list of models added in ./search_index.sh named model_list If you need to pass a custom list of model edit the model_list in ./search_index.sh or run python projectile/manage.py es_index --rebuild/--populate -f --single --custom_list 'account.Transaction' 'clinic.Service'(no comma please)
1. ./search_index.sh --rebuild -f --single --custom_list (will rebuild all documents from model_list )
2. ./search_index.sh --populate -f --single --custom_list (will populate all documents from model_list )
3. ./search_index.sh --delete -f --single --custom_list (will delete all index from model_list )
4. ./search_index.sh --create -f --single --custom_list (will create all index from model_list )
N.B: No need to add --settings=projectile.settings_live, django will find the settings from DJANGO_SETTINGS_MODULE available in .env
'

declare -a model_list
model_list=(pharmacy.Product
account.AccountCheque
account.Accounts
account.PatientBill
account.TransactionHead
account.PayableToPerson
clinic.AppointmentSchedule
clinic.AppointmentScheduleMissed
clinic.Bed
clinic.BedSection
clinic.DiagnosticTestSample
clinic.InvestigationField
clinic.PatientAdmission
clinic.ReportFieldCategory
clinic.Service
clinic.ServiceConsumedGroup
clinic.SubService
clinic.SubServiceReportField
clinic.SubServiceReportFieldNormalValue
clinic.TreatmentSession
clinic.Ward
clinic.OrganizationDepartment
core.Department
core.EmployeeDesignation
core.Organization
core.Person
core.PersonOrganization
pharmacy.EmployeeAccountAccess
pharmacy.EmployeeStorepointAccess
pharmacy.ProductForm
pharmacy.ProductGeneric
pharmacy.ProductGroup
pharmacy.ProductManufacturingCompany
pharmacy.ProductSubgroup
pharmacy.Purchase
pharmacy.Sales
pharmacy.StockAdjustment
pharmacy.StockTransfer
pharmacy.StorePoint
pharmacy.Unit
pharmacy.ProductCategory
prescription.Diagnosis
prescription.DiagnosisDepartment
prescription.Dose
prescription.LabTest
prescription.PhysicalTest
prescription.Prescription
prescription.Symptom
prescription.PrescriptionAdditionalInfo
clinic.AppointmentTreatmentSession
clinic.ServiceConsumed
account.Transaction
pharmacy.ProductDisbursementCause
core.SalaryHead
core.SalaryGrade)

ARGS="$*"
if [[ "$*" == *--custom_list* ]]
then
    ARGS="$* ${model_list[@]}"
fi

python projectile/manage.py es_index $ARGS