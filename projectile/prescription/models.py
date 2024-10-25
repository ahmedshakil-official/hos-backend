from __future__ import unicode_literals

from enumerify import fields

from django.utils.translation import gettext_lazy as _
from django.db.models.signals import pre_save
from django.db import models

from common.enums import Status, DiscardType
from common.models import (
    CreatedAtUpdatedAtBaseModel,
    CreatedAtUpdatedAtBaseModelWithOrganization,
    NameSlugDescriptionBaseOrganizationWiseModel,
)
from core.models import Person, PersonOrganization
from pharmacy.models import Product

from .enums import (
    PrescriptionType,
    TestState,
    PrescriptionPosition,
    DiagnosisType,
    UsageType,
)

# pylint: disable=old-style-class, no-init
class Symptom(NameSlugDescriptionBaseOrganizationWiseModel):

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.get_name()


class LabTest(NameSlugDescriptionBaseOrganizationWiseModel):

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.get_name()


class OrganizationWiseDiscardedLabTest(CreatedAtUpdatedAtBaseModelWithOrganization):
    # lab_test is current usage item
    lab_test = models.ForeignKey(
        LabTest,
        models.DO_NOTHING,
        blank=False,
        null=False,
        related_name='organization_wise_discarded_lab_test'
    )
    # parent is edited, merged or deleted item, this item will be discarded
    parent = models.ForeignKey(
        LabTest,
        models.DO_NOTHING,
        blank=False,
        null=False,
        related_name='organization_wise_discarded_parent_lab_test'
    )
    entry_type = fields.SelectIntegerField(
        blueprint=DiscardType,
        default=DiscardType.EDIT
    )

    class Meta:
        index_together = (
            'organization',
            'lab_test',
        )
        verbose_name_plural = "Organization's Discarded Lab Tests"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"Organization: {}, Base: {}, Lab Test: {}".format(
            self.organization,
            self.lab_test,
            self.parent
        )


class PhysicalTest(NameSlugDescriptionBaseOrganizationWiseModel):

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.get_name()


class OrganizationWiseDiscardedPhysicalTest(CreatedAtUpdatedAtBaseModelWithOrganization):
    # base is current usage item
    physical_test = models.ForeignKey(
        PhysicalTest,
        models.DO_NOTHING,
        blank=False,
        null=False,
        related_name='organization_wise_discarded_physical_test'
    )
    # physical_test is edited, merged or deleted item
    parent = models.ForeignKey(
        PhysicalTest,
        models.DO_NOTHING,
        blank=False,
        null=False,
        related_name='organization_wise_discarded_parent_physical_test'
    )
    entry_type = fields.SelectIntegerField(
        blueprint=DiscardType,
        default=DiscardType.EDIT
    )

    class Meta:
        index_together = (
            'organization',
            'physical_test',
        )
        verbose_name_plural = "Organization's Discarded Physical Tests"

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"Organization: {}, Base: {}, Physical Test: {}".format(
            self.organization,
            self.physical_test,
            self.parent
        )


class Diagnosis(NameSlugDescriptionBaseOrganizationWiseModel):
    diagnosis_department = models.ForeignKey(
        'DiagnosisDepartment', models.DO_NOTHING,
        blank=False, null=False,
        related_name="department_of_diagnosis")
    dependency_disease = models.BooleanField(
        default=False,
        help_text=_('Trace a diagnosis have dependency or not')
    )
    remarks = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        ordering = ('name',)
        verbose_name_plural = "Diagnoses"

    def __str__(self):
        return self.get_name()


class DiagnosisDepartment(NameSlugDescriptionBaseOrganizationWiseModel):

    class Meta:
        ordering = ('name',)
        verbose_name = _('Department of Diagnosis')
        verbose_name_plural = "Department of Diagnoses"

    def __str__(self):
        return self.get_name()


class Dose(NameSlugDescriptionBaseOrganizationWiseModel):

    class Meta:
        ordering = ('name',)
        verbose_name_plural = "Doses"

    def __str__(self):
        return self.get_name()

class PrescriptionAdditionalInfo(NameSlugDescriptionBaseOrganizationWiseModel):
    usage = fields.SelectIntegerField(
        blueprint=UsageType, default=UsageType.ONE_TIME)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.get_name()


class Prescription(CreatedAtUpdatedAtBaseModelWithOrganization):
    patient = models.ForeignKey(
        Person, models.DO_NOTHING, related_name="patient")
    person_organization_patient = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='patient_prescription_person_organization',
        blank=True,
        null=True,
        verbose_name=('patient in person organization'),
        db_index=True
    )
    patient_service_consumed = models.ForeignKey(
        'clinic.ServiceConsumed',
        models.DO_NOTHING,
        related_name='prescription_service_consumeds',
        blank=True,
        null=True,
        default=None
        )
    patient_admission = models.ForeignKey(
        'clinic.PatientAdmission',
        models.DO_NOTHING,
        related_name='prescription_for_inhouse_patient',
        blank=True,
        null=True,
        default=None
        )
    prescriber = models.ForeignKey(
        Person,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="prescriber"
    )
    person_organization_prescriber = models.ForeignKey(
        PersonOrganization, models.DO_NOTHING,
        related_name='prescriber_prescription_person_organization',
        blank=True,
        null=True,
        verbose_name=('prescriber in person organization'),
        db_index=True
    )

    diagnosis_history = models.CharField(
        max_length=2048,
        blank=True,
        null=True,
        verbose_name=('patient previous diagnosis'),
        help_text='Previous illness history'
    )

    notes = models.TextField(blank=True)
    type = fields.SelectIntegerField(
        blueprint=PrescriptionType, default=PrescriptionType.NORMAL)
    next_visit = models.DateTimeField(blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)

    # to-do: remove this for_initial data variable as this is was not used
    for_initial_data = models.IntegerField(default=0)

    symptoms = models.ManyToManyField(
        Symptom, through='prescription.PrescriptionSymptom')
    lab_tests = models.ManyToManyField(
        LabTest, through='prescription.PrescriptionLabTest')
    physical_tests = models.ManyToManyField(
        PhysicalTest, through='prescription.PrescriptionPhysicalTest')
    diagnoses = models.ManyToManyField(
        Diagnosis, through='prescription.PrescriptionDiagnosis')
    prescription_additional_info = models.ManyToManyField(
        PrescriptionAdditionalInfo, through='prescription.PrescriptionExtraInfo')
    instruction = models.TextField(blank=True, null=True)
    origin = models.ForeignKey(
        'self', models.DO_NOTHING, blank=True, null=True, related_name="base_origin")
    parent = models.ForeignKey(
        'self', models.DO_NOTHING, blank=True, null=True, related_name="immediate_parent")
    current_status = fields.SelectIntegerField(
        blueprint=PrescriptionPosition, default=PrescriptionPosition.LATEST)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"ID: {}, Patient: {}, Prescriber: {}, Date: {} ".format(
            self.id,
            self.patient_id,
            self.prescriber_id,
            self.date
        )


class PrescriptionTreatment(CreatedAtUpdatedAtBaseModel):
    prescription = models.ForeignKey(
        Prescription, models.DO_NOTHING, related_name='treatments')
    product = models.ForeignKey(Product, models.DO_NOTHING)
    dose = models.ForeignKey(
        Dose,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="doses"
    )
    interval = models.CharField(max_length=255, blank=True, null=True)
    duration = models.CharField(max_length=255, blank=True, null=True)
    method = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"ID: {}, product: {}".format(self.id, self.product_id)


class DietSchedule(CreatedAtUpdatedAtBaseModel):
    person = models.ForeignKey(
        Person, models.DO_NOTHING, blank=False, null=False, related_name='diet_person')
    diet_time = models.TimeField(blank=False, null=False)
    label = models.CharField(blank=True, null=True, max_length=255)
    reminder = fields.SelectIntegerField(
        blueprint=Status, default=Status.ACTIVE)
    status = fields.SelectIntegerField(
        blueprint=Status, default=Status.ACTIVE)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"ID: {}, person: {}. time: {}".format(self.id, self.person_id, self.reminder)


class MedicineSchedule(CreatedAtUpdatedAtBaseModel):
    person = models.ForeignKey(
        Person, models.DO_NOTHING, blank=False, null=False, related_name='medicine_person')
    product = models.CharField(blank=False, null=False, max_length=255)
    dose = models.CharField(blank=False, null=False, max_length=255)
    interval = models.CharField(max_length=255)
    duration = models.CharField(max_length=255)
    method = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    reminder = fields.SelectIntegerField(
        blueprint=Status, default=Status.ACTIVE)
    status = fields.SelectIntegerField(
        blueprint=Status, default=Status.ACTIVE)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"ID: {}, person: {}. time: {}".format(self.id, self.person_id, self.product)


class PrescriptionConnector(CreatedAtUpdatedAtBaseModel):
    prescription = models.ForeignKey(Prescription, models.DO_NOTHING, related_name='%(class)s_list')

    class Meta:
        abstract = True

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"ID: {}, prescription: {}".format(self.id, self.prescription_id)


class PrescriptionSymptom(PrescriptionConnector):
    relative = models.ForeignKey(Symptom, models.DO_NOTHING)

    class Meta:
        index_together = (
            'prescription',
            'relative',
        )
        unique_together = (
            'prescription',
            'relative',
        )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"ID: {}, relative: {}".format(self.id, self.relative_id)

class PrescriptionExtraInfo(PrescriptionConnector):
    relative = models.ForeignKey(PrescriptionAdditionalInfo, models.DO_NOTHING)
    info = models.CharField(max_length=512, blank=True, null=True)

    class Meta:
        index_together = (
            'prescription',
            'relative',
        )
        unique_together = (
            'prescription',
            'relative',
        )
    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"ID: {}, relative: {}".format(self.id, self.relative_id)


class PrescriptionDiagnosis(CreatedAtUpdatedAtBaseModel):
    prescription = models.ForeignKey(
        Prescription, models.DO_NOTHING, related_name='diagnosis_list')
    relative = models.ForeignKey(Diagnosis, models.DO_NOTHING)
    remarks = models.CharField(max_length=256, blank=True, null=True)
    type = fields.SelectIntegerField(
        blueprint=DiagnosisType, default=DiagnosisType.CURRENT, help_text='Diagnosis Type'
    )
    class Meta:
        index_together = (
            'prescription',
            'relative',
        )
        unique_together = (
            'prescription',
            'relative',
        )

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"ID: {}, relative: {}".format(self.id, self.relative_id)


class PrescriptionPhysicalTest(CreatedAtUpdatedAtBaseModel):
    prescription = models.ForeignKey(
        Prescription, models.DO_NOTHING, related_name='physical_tests_list')
    relative = models.ForeignKey(PhysicalTest, models.DO_NOTHING)
    result = models.CharField(max_length=255, blank=True, null=True)
    taken_at = models.DateTimeField(blank=True, null=True)
    state = fields.SelectIntegerField(
        blueprint=TestState, default=TestState.PRE)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"ID: {}, prescription: {}".format(self.id, self.prescription_id)


class PrescriptionLabTest(CreatedAtUpdatedAtBaseModel):
    prescription = models.ForeignKey(
        Prescription, models.DO_NOTHING, related_name='lab_tests_list')
    relative = models.ForeignKey(LabTest, models.DO_NOTHING)
    result = models.CharField(max_length=255, blank=True, null=True)
    taken_at = models.DateTimeField(blank=True, null=True)
    state = fields.SelectIntegerField(
        blueprint=TestState, default=TestState.PRE)

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return u"ID: {}, prescription: {}".format(self.id, self.prescription_id)
