from __future__ import unicode_literals
from enumerify import fields

from django.db import models
from django.db.models.signals import post_save, pre_save
from django.core.validators import MinValueValidator, MaxValueValidator

from common.models import (
    CreatedAtUpdatedAtBaseModel,
    NameSlugDescriptionBaseOrganizationWiseModel,
    CreatedAtUpdatedAtBaseModelWithOrganization,
    OrganizationWiseCreatedAtUpdatedAtBaseModelWithGlobal,
)
from common.fields import TimestampImageField
from common.utils import clean_image
from common.enums import Status, GlobalCategory, DiscardType

from common.validators import (
    is_employee,
    admin_validate_unique_name_with_org,
    is_person_or_employee,
)
from core.enums import PersonGender
from core.models import (
    Person,
    PersonOrganization,
)
from prescription.models import LabTest
from pharmacy.models import Product

from .mixins import ImageThumbFieldMixin

from .enums import (
    ServiceType,
    ConfirmedType,
    PatientAdmissionBedStatus,
    EmployeeAttendanceType,
    BedStatus,
    ServiceConsumedPriority,
    BedType,
    ServiceConsumedType,
    ServiceConsumedSubType,
    DaysChoice,
    PaymentType,
    AppointmentType,
    AppointmentKind
)


class Ward(NameSlugDescriptionBaseOrganizationWiseModel):

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.get_name()


class BedSection(CreatedAtUpdatedAtBaseModelWithOrganization):
    section_name = models.CharField(max_length=256, blank=False, null=False)

    def __str__(self):
        return self.section_name


class EmployeeBedSectionAccess(CreatedAtUpdatedAtBaseModelWithOrganization):
    employee = models.ForeignKey(
        Person,
        models.DO_NOTHING,
        blank=False,
        null=False,
        related_name='section_access_employee'
    )

    person_organization = models.ForeignKey(
        PersonOrganization,
        models.DO_NOTHING,
        blank=True,
        null=True,
        db_index=True,
        related_name='section_access_person_organization',
        verbose_name=('employee in person organization'),
    )
    bed_section = models.ForeignKey(
        BedSection,
        models.DO_NOTHING,
        blank=False,
        null=False,
        related_name='employee_section'
    )
    access_status = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Employee Bed Section Access"
        verbose_name_plural = "Employee Bed Section Accesses"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} - {}".format(
            self.id, self.person_organization_id, self.bed_section_id)


class Bed(NameSlugDescriptionBaseOrganizationWiseModel):
    ward = models.ForeignKey(Ward, models.DO_NOTHING, blank=True, null=True, default=None)
    bed_section = models.ForeignKey(
        BedSection, models.DO_NOTHING, blank=True, null=True, default=None)
    cost_per_day = models.FloatField(blank=False, null=False, default='0.00')
    is_occupied = fields.SelectIntegerField(
        blueprint=BedStatus, default=BedStatus.FREE)
    bed_type = fields.SelectIntegerField(
        blueprint=BedType, default=BedType.ADMISSION_BED)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return "{} / {}".format(self.name, self.bed_section_id)

    def clean(self):
        admin_validate_unique_name_with_org(self, 'bed_section', bed_section=self.bed_section)


class PatientAdmission(CreatedAtUpdatedAtBaseModelWithOrganization):
    admission_date = models.DateTimeField(blank=False, null=False)
    patient = models.ForeignKey(
        Person, models.DO_NOTHING,
        related_name='admited_patient',
        db_index=True
    )

    person_organization_patient = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='patient_person_organization',
        blank=True,
        null=True,
        verbose_name=('patient person organization'),
        db_index=True
    )

    department = models.ForeignKey(
        'prescription.DiagnosisDepartment', models.DO_NOTHING,
        null=True,
        blank=True,
        related_name='diagnosis_department',
        db_index=True
    )
    consultant = models.ForeignKey(
        Person,
        models.DO_NOTHING,
        null=True,
        blank=True,
        related_name='admission_consultant',
        db_index=True
    )

    person_organization_consultant = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='consultant_person_organization',
        blank=True,
        null=True,
        verbose_name=('consultant person organization'),
        db_index=True
    )

    cost = models.FloatField(blank=False, null=False, default='0.00')
    discount = models.FloatField(blank=False, null=False, default='0.00')
    payable = models.FloatField(blank=False, null=False, default='0.00')
    paid_amount = models.FloatField(blank=False, null=False, default=0.00)
    bed_charge = models.FloatField(blank=False, null=False, default=0.00)
    release_date = models.DateTimeField(blank=True, null=True, default=None)
    discharge_summary = models.TextField(blank=True, null=True, default=None)
    remarks = models.CharField(max_length=256)
    referrer = models.ForeignKey(
        Person,
        models.DO_NOTHING,
        null=True,
        blank=True,
        default=None,
        related_name='admission_referrer'
    )
    bill = models.ForeignKey(
        'account.PatientBill',
        models.DO_NOTHING,
        blank=True, null=True,
        related_name='admission_on_patient_bill',
        db_index=True
    )
    person_organization_referrer = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        null=True,
        blank=True,
        default=None,
        verbose_name=('referrer person organization'),
        related_name='referrer_person_organization',
    )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.patient_id, self.admission_date, self.release_date)

    def get_bed(self):
        if self.admission.first():
            bed = self.admission.first().bed
            return bed
        return None


class PatientAdmissionBed(CreatedAtUpdatedAtBaseModel):
    patient_admission = models.ForeignKey(
        PatientAdmission, models.DO_NOTHING, related_name='admission')
    bed = models.ForeignKey(Bed, models.DO_NOTHING,
                            related_name="admission_bed")
    cost = models.FloatField(blank=False, null=False, default='0.00')
    admission_date = models.DateTimeField(blank=False, null=False)
    release_date = models.DateTimeField(blank=True, null=True, default=None)
    total_cost = models.FloatField(blank=False, null=False, default='0.00')
    status = fields.SelectIntegerField(
        blueprint=PatientAdmissionBedStatus, default=PatientAdmissionBedStatus.INITIALLY_MOVED)
    remarks = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {}".format(self.patient_admission, self.bed)


class AdmissionConsultant(CreatedAtUpdatedAtBaseModelWithOrganization):
    admission = models.ForeignKey(
        PatientAdmission, models.DO_NOTHING, related_name='admission_by_consultant')
    consultant = models.ForeignKey(
        Person, models.DO_NOTHING, null=True, blank=True,
        related_name='consultant_of_admission')
    date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"Date: {}, admission: {}, consultant: {}".format(
            self.date, self.admission_id, self.consultant_id)

    def save(self, *args, **kwargs):
        if self.date is None:
            self.date = self.admission.admission_date
        super(AdmissionConsultant, self).save(*args, **kwargs)


class TreatmentSession(NameSlugDescriptionBaseOrganizationWiseModel):
    start_time = models.TimeField(blank=True, null=True)
    send_sms = models.BooleanField(default=False)
    send_sms_before = models.DurationField(blank=True, null=True)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return self.name


class Service(NameSlugDescriptionBaseOrganizationWiseModel):
    type = fields.SelectIntegerField(
        blueprint=ServiceType, default=ServiceType.OTHERS)
    sub_type = fields.SelectIntegerField(
        blueprint=ServiceConsumedSubType, default=ServiceConsumedSubType.OTHERS
    )
    discount = models.FloatField(
        default=0.0,
        validators=[MaxValueValidator(100), MinValueValidator(0)],
        help_text='discount in percentage(%)'
    )

    def __str__(self):
        return self.get_name()


class SubService(NameSlugDescriptionBaseOrganizationWiseModel):
    service = models.ForeignKey(
        Service, models.DO_NOTHING, blank=True, null=True)
    labtest = models.ForeignKey(
        LabTest,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='sub_service_lab_test'
    )
    price = models.FloatField(validators=[MinValueValidator(0.0)])
    transaction_head = models.ForeignKey(
        'account.TransactionHead', models.DO_NOTHING,
        blank=True, null=True, default=None, related_name='sub_services'
    )
    code_name = models.CharField(max_length=30, blank=True, null=True)
    processing_time = models.PositiveIntegerField(
        default=0, help_text='This field will store processing time in minute.'
    )
    image_flag = models.BooleanField(default=False)
    samples = models.ManyToManyField(
        'clinic.DiagnosticTestSample', through='clinic.SubServiceSample',
        related_name='subservices_of_sample'
    )
    global_category = fields.SelectIntegerField(
        blueprint=GlobalCategory,
        default=GlobalCategory.DEFAULT
    )
    remarks = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    def __str__(self):
        try:
            return u"#{}: {} - {}".format(self.id, self.service_id, self.labtest_id)
        except NameError:
            return u"#{}: {} - {}".format(self.id, self.service_id, self.name)


class OrganizationWiseDiscardedSubService(CreatedAtUpdatedAtBaseModelWithOrganization):
    # sub_service is current usage item
    sub_service = models.ForeignKey(
        SubService,
        models.DO_NOTHING,
        blank=False,
        null=False,
        related_name='organization_wise_discarded_sub_service'
    )
    # parent is edited, merged or deleted item
    parent = models.ForeignKey(
        SubService,
        models.DO_NOTHING,
        blank=False,
        null=False,
        related_name='organization_wise_discarded_parent_sub_service'
    )
    entry_type = fields.SelectIntegerField(
        blueprint=DiscardType,
        default=DiscardType.EDIT
    )

    class Meta:
        index_together = (
            'organization',
            'sub_service',
        )
        verbose_name_plural = "Organization's Discarded Sub Services"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"Organization: {}, Base: {}, SubService: {}".format(
            self.organization_id,
            self.sub_service_id,
            self.parent_id
        )


class DiagnosticTestSample(NameSlugDescriptionBaseOrganizationWiseModel):
    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name = "Diagnostic Test Sample"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return self.name


class SubServiceSample(CreatedAtUpdatedAtBaseModelWithOrganization):
    sub_service = models.ForeignKey(
        'clinic.SubService', models.DO_NOTHING,
        blank=False, null=False, related_name="sample_of_subservice")
    sample = models.ForeignKey(
        'clinic.DiagnosticTestSample', models.DO_NOTHING,
        blank=False, null=False, related_name="subservice_of_sample")

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name = "Sample of SubService"
        verbose_name_plural = "Samples of SubServices"
        index_together = (
            'sub_service',
            'sample',
        )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.id, self.sub_service_id, self.sample_id)


class SubServiceSampleCollection(CreatedAtUpdatedAtBaseModelWithOrganization):
    sample_label = models.CharField(max_length=30, blank=True, null=True)
    collection_date = models.DateTimeField(blank=True, null=True, default=None)
    service_consumed = models.ForeignKey(
        'clinic.ServiceConsumed', models.DO_NOTHING,
        blank=False, null=False, related_name='samples_of_service_consumed'
    )
    sub_service_sample = models.ForeignKey(
        'clinic.SubServiceSample', models.DO_NOTHING,
        blank=False, null=False, related_name='collections_of_sample'
    )

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name = "Sample Collection Of SubService"
        verbose_name_plural = "Samples Collection Of SubServices"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {} / {}".format(
            self.id, self.sample_label, self.service_consumed_id, self.sub_service_sample_id
        )


class InvestigationField(NameSlugDescriptionBaseOrganizationWiseModel):
    priority = models.PositiveIntegerField(default=0, help_text='Highest comes first.')
    price = models.FloatField(validators=[MinValueValidator(0.0)], default=0.0)
    standard_reference = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=512, blank=True, null=True)

    class Meta:
        ordering = ('-priority',)
        verbose_name = "Investigation Field"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"ID: {}, Name: {}, Price: {}".format(self.id, self.name, self.price)


class ReportFieldCategory(NameSlugDescriptionBaseOrganizationWiseModel):
    priority = models.PositiveIntegerField(default=0, help_text='Highest comes first.')

    # pylint: disable=old-style-class, no-init
    class Meta:
        ordering = ('-priority',)
        verbose_name_plural = "Report Field Categories"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}".format(self.name)


class SubServiceReportField(NameSlugDescriptionBaseOrganizationWiseModel):
    sub_service = models.ForeignKey(
        SubService, models.DO_NOTHING, blank=False,
        null=False, related_name='report_fields_of_labtest'
    )
    investigation_field = models.ForeignKey(
        InvestigationField,
        models.DO_NOTHING,
        related_name='report_of_investigation',
        blank=True,
        null=True,
        default=None,
        db_index=True
    )
    category = models.ForeignKey(
        ReportFieldCategory,
        models.DO_NOTHING,
        related_name='report_of_category',
        blank=True,
        null=True,
        default=None,
        db_index=True
    )
    category_name = models.CharField(max_length=255, blank=True, null=True)
    price = models.FloatField(validators=[MinValueValidator(0.0)], default=0)
    show_category = models.BooleanField(default=True)
    category_priority = models.PositiveIntegerField(
        default=0, help_text='Highest comes first.')
    field_priority = models.PositiveIntegerField(
        default=0, help_text='Highest comes first.')

    # pylint: disable=old-style-class, no-init
    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"ID: {}, Labtest: {}, Field: {}".format(self.id, self.sub_service.name, self.name)

    def clean(self):
        admin_validate_unique_name_with_org(
            self, 'sub_service', 'investigation_field', 'category',
            sub_service=self.sub_service, category=self.category
        )


    def save(self, *args, **kwargs):
        if self.category:
            self.category_name = self.category.name
        super(SubServiceReportField, self).save(*args, **kwargs)


class SubServiceReportFieldNormalValue(OrganizationWiseCreatedAtUpdatedAtBaseModelWithGlobal):
    sub_service_report_field = models.ForeignKey(
        SubServiceReportField, models.DO_NOTHING,
        blank=False, null=False, related_name='normal_value_of_report_field'
    )
    gender = fields.SelectIntegerField(
        blueprint=PersonGender, default=PersonGender.ANY)
    age_min = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    age_max = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    value_min = models.CharField(max_length=2000, blank=True, null=True)
    value_max = models.CharField(max_length=2000, blank=True, null=True)
    unit = models.CharField(max_length=255, blank=True, null=True)

    # pylint: disable=old-style-class, no-init
    class Meta:
        ordering = ('sub_service_report_field',)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"ID: {}, Feild Name: {}".format(self.id, self.sub_service_report_field_id)

    # def save(self, *args, **kwargs):
    #     if self.value_min:
    #         report = self.sub_service_report_field.report_value_of_field
    #         if report.exists():
    #             if self.unit:
    #                 report.update(unit=self.unit)
    #             report.update(standard_reference=self.value_min)
    #     super(SubServiceReportFieldNormalValue, self).save(*args, **kwargs)


class ServiceConsumed(CreatedAtUpdatedAtBaseModelWithOrganization):
    person = models.ForeignKey(
        Person,
        models.DO_NOTHING,
        related_name='consumed_person',
        db_index=True
    )

    person_organization_patient = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='service_consumed_patient_person_organization',
        blank=True,
        null=True,
        verbose_name=('patient in person organization'),
        db_index=True
    )

    patient_admission = models.ForeignKey(
        PatientAdmission,
        models.DO_NOTHING,
        related_name='service_for_inhouse_patient',
        blank=True,
        null=True,
        default=None,
        db_index=True
    )
    date = models.DateTimeField()
    subservice = models.ForeignKey(
        SubService,
        models.DO_NOTHING,
        db_index=True
    )
    price = models.FloatField(validators=[MinValueValidator(0.00)])
    discount = models.FloatField(validators=[MinValueValidator(0.00)])
    paid = models.FloatField(default=0.00, validators=[MinValueValidator(0.00)])
    provider = models.ForeignKey(
        Person,
        models.DO_NOTHING,
        related_name='provider_person',
        null=True,
        blank=True,
        default=None,
        db_index=True
    )

    person_organization_provider = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='service_provider_person_organization',
        blank=True,
        null=True,
        verbose_name=('provider in person organization'),
        db_index=True
    )

    remarks = models.CharField(max_length=256, blank=True, null=True)
    reference = models.ForeignKey(
        Person,
        models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        related_name='service_referer',
        db_index=True
    )

    person_organization_reference = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='reference_provider_person_organization',
        blank=True,
        null=True,
        verbose_name=('reference in person organization'),
        db_index=True
    )

    second_reference = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='second_referer',
        blank=True,
        null=True,
        verbose_name=('reference from other person'),
        db_index=True
    )

    referer_honorarium = models.FloatField(
        null=False,
        blank=False,
        default=0.00,
        validators=[MinValueValidator(0.00)],
        db_index=True,
        help_text='Honorarium in percentage (%)'
    )

    allow_honorarium = models.BooleanField(
        null=False,
        blank=False,
        default=False,
        db_index=True
    )

    honorarium_paid = models.BooleanField(
        null=False,
        blank=False,
        default=False,
        db_index=True
    )

    payable = models.BooleanField(default=True)
    priority = fields.SelectIntegerField(
        blueprint=ServiceConsumedPriority, default=ServiceConsumedPriority.NORMAL)
    service_consumed_type = fields.SelectIntegerField(
        blueprint=ServiceConsumedType,
        default=ServiceConsumedType.DEFAULT)
    service_consumed_group = models.ForeignKey(
        'ServiceConsumedGroup',
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='service_consumed_group',
        db_index=True
    )
    sample_collection_date = models.DateTimeField(blank=True, null=True, default=None)
    sample_test_date = models.DateTimeField(blank=True, null=True, default=None)

    subservice_samples = models.ManyToManyField(
        'clinic.SubServiceSample', through='clinic.SubServiceSampleCollection',
        related_name='service_consumed_of_subservice_sample')
    tentative_delivery_date = models.DateTimeField(blank=True, null=True, default=None)
    report_delivered = models.BooleanField(blank=True, default=False, null=True)
    estimated_delivery_date = models.DateTimeField(blank=True, null=True, default=None)
    department = models.ForeignKey(
        'clinic.OrganizationDepartment',
        models.DO_NOTHING,
        blank=True, null=True,
        related_name='service_consumeds',
    )
    prescription = models.ForeignKey(
        'prescription.Prescription',
        models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        related_name='service_consumed',
        db_index=True
    )
    tested_by = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='service_consumeds_of_tester',
        default=None,
        blank=True,
        null=True,
        verbose_name=('tested by in person organization'),
        db_index=True
    )
    report_verified_by = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='service_consumeds_of_report_verifier',
        default=None,
        blank=True,
        null=True,
        verbose_name=('report verifier in person organization'),
        db_index=True
    )
    referrer_deduction = models.FloatField(
        default=0.00,
        help_text='deducted amount from referrer'
    )
    special_discount = models.FloatField(
        default=0.00,
        help_text='total person discount'
    )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {} {}- {}".format(
            self.id, self.date, self.subservice.name, self.person_id, self.provider_id
        )


class ServiceConsumedImage(CreatedAtUpdatedAtBaseModel, ImageThumbFieldMixin):
    service_consumed = models.ForeignKey(
        ServiceConsumed, models.DO_NOTHING, blank=False, null=False)
    image = TimestampImageField(upload_to='service/pic', blank=False, null=False)
    priority = models.PositiveIntegerField(default=0, help_text='Highest comes first.')
    caption = models.TextField(blank=True, null=True)

    def __str__(self):
        return u'{} -> {}'.format(self.service_consumed_id, self.image.name)

    # pylint: disable=old-style-class, no-init
    class Meta:
        ordering = ('-priority',)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.create_thumbnails()
        self.image = clean_image(self.image)
        super(ServiceConsumedImage, self).save(*args, **kwargs)


class ServiceConsumedGroup(CreatedAtUpdatedAtBaseModelWithOrganization):
    discount = models.FloatField(blank=False, null=False, default='0.00')
    remarks = models.CharField(max_length=256)
    tentative_delivery_date = models.DateTimeField(blank=True, null=True, default=None)
    report_delivered = models.BooleanField(blank=True, default=False, null=True)
    payment_type = fields.SelectIntegerField(
        blueprint=PaymentType, default=PaymentType.CASH)
    total = models.FloatField(default=0.00)
    payable = models.FloatField(default=0.00)
    paid = models.FloatField(default=0.00, validators=[MinValueValidator(0.00)])
    bill = models.ForeignKey(
        'account.PatientBill',
        models.DO_NOTHING,
        blank=True, null=True,
        related_name='service_group_on_patient_bill',
        db_index=True
    )
    sub_services = models.TextField(
        max_length=2048, null=True, blank=True,)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"{}, discount: {}".format(self.pk, self.discount)

    def get_due_amount_of_service_consumed(self):
        services = self.service_consumed_group.all()
        transactions = self.service_consumed_group_transaction.filter(status=Status.ACTIVE)
        try:
            service_amount = sum([item.price for item in services])
        except:
            service_amount = 0
        try:
            paid_amount = sum([item.amount for item in transactions])
        except:
            paid_amount = 0
        return  service_amount - paid_amount

    # def get_person_organization_person(self):
    #     try:
    #         return self.service_consumed_group.first().person_organization_patient
    #     except AttributeError:
    #         return None

    def get_service_consumed_date(self):
        try:
            return self.service_consumed_group.values('date')[0]['date']
        except IndexError:
            return None

    def get_service_consumeds(self):
        return self.service_consumed_group.select_related(
            'subservice'
        ).filter(status=Status.ACTIVE)

    # def get_admission_of_service_consumed(self):
    #     try:
    #         return self.service_consumed_group.first().patient_admission
    #     except AttributeError:
    #         return None


class ServiceConsumedGroupSalesTransation(CreatedAtUpdatedAtBaseModelWithOrganization):
    """
    This model will keep track of service consumed, sales and transaction
    """
    service_consumed_group = models.ForeignKey(
        'ServiceConsumedGroup',
        models.DO_NOTHING,
        blank=True, null=True,
        related_name='group_service_consumed',
        db_index=True
    )
    sales = models.ForeignKey(
        'pharmacy.Sales',
        models.DO_NOTHING,
        blank=True, null=True,
        related_name='sales_for_service_consumed_group',
        db_index=True
    )
    transaction_group = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=('unique code for group transaction')
    )

    # pylint: disable=old-style-class, no-init, R0903, missing-docstring
    class Meta:
        verbose_name_plural = "ServiceConsumeds Sales Transation"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}".format(self.id)


class SubServiceReport(OrganizationWiseCreatedAtUpdatedAtBaseModelWithGlobal):
    service_consumed = models.ForeignKey(
        ServiceConsumed, models.DO_NOTHING, blank=False, null=False,
        related_name='report_of_service_consumed')
    employee = models.ForeignKey(
        Person, models.DO_NOTHING, related_name='sub_service_report_provider',
        null=True, blank=True, default=None)
    person_organization_employee = models.ForeignKey(
        PersonOrganization,
        models.DO_NOTHING,
        null=True,
        blank=True,
        default=None,
        db_index=True,
        related_name='sub_service_report_provider_person_organization',
        verbose_name='sub service report provider in person organization'
    )
    date = models.DateTimeField(blank=True, null=True, default=None)
    sub_service_report_field = models.ForeignKey(
        SubServiceReportField, models.DO_NOTHING, blank=False, null=False,
        related_name='report_value_of_field')
    result = models.CharField(max_length=1024, blank=False, null=False)
    standard_reference = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {} - {}".format(
            self.id, self.date, self.sub_service_report_field_id, self.result
        )

    def save(self, *args, **kwargs):
        reference = self.sub_service_report_field.normal_value_of_report_field.first()
        if not self.pk:
            if self.standard_reference:
                if reference:
                    reference.value_min = self.standard_reference
                    reference.unit = self.unit
                    reference.save()
                else:
                    SubServiceReportFieldNormalValue.objects.create(
                        sub_service_report_field=self.sub_service_report_field,
                        value_min=self.standard_reference,
                        value_max=self.standard_reference,
                        unit=self.unit
                    )
        super(SubServiceReport, self).save(*args, **kwargs)


class AppointmentTreatmentSession(CreatedAtUpdatedAtBaseModelWithOrganization):
    person = models.ForeignKey(
        Person, models.DO_NOTHING,
        db_index=True,
        related_name='person_of_appointment',
    )
    appointment_date = models.DateField()
    treatment_session = models.ForeignKey(
        TreatmentSession, models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        db_index=True
    )
    bed = models.ForeignKey(
        Bed, models.DO_NOTHING,
        blank=True,
        null=True,
        default=None,
        db_index=True
    )
    price = models.FloatField()
    discount = models.FloatField()
    remarks = models.CharField(max_length=256, blank=True, null=True)
    appointment_with = models.ForeignKey(
        Person,
        models.DO_NOTHING,
        related_name='appointment_with',
        blank=True,
        null=True,
        db_index=True
    )
    person_organization = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='appointment_treatment_person_organization',
        blank=True,
        null=True,
        verbose_name=('appointment of person of organization'),
        db_index=True
    )

    person_organization_with = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='appointment_with_person_organization',
        blank=True,
        null=True,
        verbose_name=('appointment with in person organization'),
        db_index=True
    )


    patient_admission = models.ForeignKey(
        PatientAdmission,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='appointment_patient_admission',
        db_index=True
    )
    confirmed = fields.SelectIntegerField(
        blueprint=ConfirmedType, default=ConfirmedType.APPROVED_BY_BOTH)
    payable = models.BooleanField(default=True)
    type = fields.SelectIntegerField(
        blueprint=AppointmentType, default=AppointmentType.CONFIRMED)
    kind = fields.SelectIntegerField(
        blueprint=AppointmentKind, default=AppointmentKind.OPERATION)

    # pylint: disable=old-style-class, no-init
    # class Meta:
    #     unique_together = (('appointment_date', 'treatment_session', 'bed'),)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {} - {}".format(
            self.id,
            self.appointment_date,
            self.treatment_session,
            self.bed_id)


class AppointmentSchedule(CreatedAtUpdatedAtBaseModelWithOrganization):
    person = models.ForeignKey(
        Person, models.DO_NOTHING, validators=[is_person_or_employee],
        related_name='patient_appointment_schedules')
    days = fields.SelectIntegerField(blueprint=DaysChoice, default=DaysChoice.MONDAY)
    treatment_session = models.ForeignKey(TreatmentSession, models.DO_NOTHING)
    bed = models.ForeignKey(Bed, models.DO_NOTHING,
                            blank=True, null=True, default=None)
    price = models.FloatField(validators=[MinValueValidator(0.00)])
    discount = models.FloatField(validators=[MinValueValidator(0.00)])
    remarks = models.CharField(max_length=256, blank=True, null=True)
    appointment_with = models.ForeignKey(
        Person,
        models.DO_NOTHING,
        related_name='appointment_schedule_with',
        blank=True,
        null=True,
        validators=[is_employee])

    person_organization_with = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='appointment_schedule_with_person_organization',
        blank=True,
        null=True,
        verbose_name=('appointment with in person organization'),
        db_index=True
    )

    patient_admission = models.ForeignKey(
        PatientAdmission, models.DO_NOTHING, blank=True, null=True,
        related_name='appointment_patient_admission_schedule')
    confirmed = fields.SelectIntegerField(
        blueprint=ConfirmedType, default=ConfirmedType.APPROVED_BY_BOTH)
    payable = models.BooleanField(default=True)

    person_organization = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='appointment_schedule_person_organization',
        blank=True,
        null=True,
        verbose_name=('appointment schedule by person of organization'),
        db_index=True
    )

    last_cron_update = models.DateTimeField(blank=True, null=True, default=None)
    kind = fields.SelectIntegerField(
        blueprint=AppointmentKind, default=AppointmentKind.OPERATION)

    # pylint: disable=old-style-class, no-init
    # class Meta:
        # unique_together = (('treatment_session', 'bed'), )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {} / {}".format(
            self.id,
            self.person_id,
            self.treatment_session_id,
            self.bed_id
        )


class AppointmentScheduleMissed(CreatedAtUpdatedAtBaseModelWithOrganization):
    appointment_schedule = models.ForeignKey(
        AppointmentSchedule,
        models.DO_NOTHING,
        related_name='missed_schedule',
        blank=False, null=False)
    date = models.DateField()

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {}".format(self.id, self.appointment_schedule_id)


class AppointmentServiceConsumed(CreatedAtUpdatedAtBaseModelWithOrganization):
    appointment = models.ForeignKey(
        AppointmentTreatmentSession,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='appointment_service_consumed'
    )
    service_consumed_group = models.ForeignKey(
        ServiceConsumedGroup,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='service_consumed_with_appointment'
    )
    sales = models.ForeignKey(
        'pharmacy.Sales',
        models.DO_NOTHING,
        blank=True,
        null=True,
    )

    # pylint: disable=old-style-class, no-init
    class Meta:
        unique_together = ('service_consumed_group', 'sales',)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {}".format(self.id, self.appointment_id)

    def get_appointment_transaction(self):
        from account.models import Transaction
        try:
            return Transaction.objects.select_related(
                'accounts', 'head', 'received_by'
            ).get(appointment=self.appointment)
        except Transaction.DoesNotExist:
            return None


class DutyShift(NameSlugDescriptionBaseOrganizationWiseModel):
    entry_time = models.TimeField(blank=False, null=False)
    exit_time = models.TimeField(blank=False, null=False)

    # pylint: disable=old-style-class, no-init
    class Meta:
        unique_together = ('organization', 'name',)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {} - {}".format(
            self.id,
            self.name,
            self.entry_time,
            self.exit_time
        )


class EmployeeAttendance(CreatedAtUpdatedAtBaseModelWithOrganization):
    employee = models.ForeignKey(
        Person, models.DO_NOTHING, related_name='attendance_of',
        blank=False, null=False, default=None
    )
    date = models.DateField(blank=False, null=False)
    shift = models.ForeignKey(
        DutyShift, models.DO_NOTHING, blank=False, null=False)
    entry_time = models.DateTimeField(blank=True, null=True, default=None)
    exit_time = models.DateTimeField(blank=True, null=True, default=None)
    type = fields.SelectIntegerField(
        blueprint=EmployeeAttendanceType, default=EmployeeAttendanceType.DEFAULT)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.id, self.employee_id, self.shift_id)


class EmployeeSession(CreatedAtUpdatedAtBaseModelWithOrganization):
    employee = models.ForeignKey(
        Person, models.DO_NOTHING, related_name='session_of',
        blank=False, null=False, default=None, db_index=True)
    session = models.ForeignKey(
        TreatmentSession, models.DO_NOTHING, blank=True, null=True,
        default=None, db_index=True, related_name='sessions'
    )
    days = fields.SelectIntegerField(blueprint=DaysChoice, default=DaysChoice.MONDAY, db_index=True)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {} / {}".format(self.id, self.employee_id, self.days, self.session_id)


class OrganizationDepartment(NameSlugDescriptionBaseOrganizationWiseModel):

    # pylint: disable=old-style-class, no-init
    class Meta:
        verbose_name_plural = "organization department"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {}".format(self.id, self.name)


class ReferrerCategoryDiscountGroup(CreatedAtUpdatedAtBaseModelWithOrganization):
    honorarium = models.FloatField(
        blank=False,
        null=False,
        default='0.00',
        help_text="Store honorarium in percentage"
    )

    class Meta:
        verbose_name = "Referrer Category Discount Group"
        verbose_name_plural = "Referrer Category Discount Groups"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(
            self.id, self.referrer_category, self.discount_group_id)


class ProductOfService(CreatedAtUpdatedAtBaseModelWithOrganization):
    sub_service = models.ForeignKey(
        SubService,
        models.DO_NOTHING,
        blank=False,
        null=False,
        related_name="service_of_product"
    )
    product = models.ForeignKey(
        Product,
        models.DO_NOTHING,
        blank=False,
        null=False,
        related_name="products_of_service"
    )
    quantity = models.FloatField(default=0.0)

    class Meta:
        verbose_name = "Product of service"
        verbose_name_plural = "Products of service"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"#{}: {} / {}".format(self.id, self.sub_service_id, self.product_id)
