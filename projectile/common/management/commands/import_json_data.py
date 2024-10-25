from django.core.management.base import BaseCommand
from django.core import management


class Command(BaseCommand):
    def handle(self, **options):
        management.call_command('import_organization',
                                verbosity=0, interactive=False)
        management.call_command(
            'import_diagnosis', verbosity=0, interactive=False)
        management.call_command(
            'import_labtest', verbosity=0, interactive=False)
        management.call_command('import_physical_test',
                                verbosity=0, interactive=False)
        management.call_command(
            'import_symptom', verbosity=0, interactive=False)
        management.call_command('import_bed', verbosity=0, interactive=False)
        management.call_command(
            'import_treatment_session', verbosity=0, interactive=False)
        management.call_command(
            'import_product', verbosity=0, interactive=False)
        management.call_command(
            'import_employee', verbosity=0, interactive=False)
        management.call_command(
            'import_patient', verbosity=0, interactive=False)
        management.call_command('import_prescription',
                                verbosity=0, interactive=False)
