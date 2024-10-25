import random
import sys
from faker import Factory

from django.core.management.base import BaseCommand

from core.models import Organisation, OrganisationUser, UserProfile, Descendant
from timetracker.models import Project


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('rows', nargs='?', const=5, type=int)

    def handle(self, *args, **options):
        rows = options['rows']

        fake = Factory.create()
        access = [1, 2, 3]

        OrganisationUser.objects.all().delete()
        Descendant.objects.all().delete()
        Organisation.objects.all().delete()
        UserProfile.objects.all().delete()

        # creating a super user
        user = UserProfile.objects.create(
            email='admin@admin.com', first_name='Admin', last_name='User')
        user.is_superuser = True
        user.is_staff = True
        user.set_password('admin')
        user.save()

        # creating a organisation for admin user
        organisation = Organisation.objects.create(name="Will and Skill", organisation_no=fake.ean8(),
                                                   identifier=fake.word(), address=fake.address(),
                                                   zip_area=fake.state_abbr(), zip_code=fake.zipcode(),
                                                   country=fake.country_code())

        OrganisationUser.objects.create(organisation=organisation,
                                        profile=user, access=1, is_current=True)

        # generating user list
        for _ in range(0, rows):
            UserProfile.objects.create(
                email=fake.email(), first_name=fake.first_name(), last_name=fake.last_name())

        # generating client list
        for _ in range(0, rows):
            new_org = Organisation.objects.create(name=fake.company(), organisation_no=fake.ean8(),
                                                  identifier=fake.word(), address=fake.address(),
                                                  zip_area=fake.state_abbr(), zip_code=fake.zipcode(),
                                                  country=fake.country_code())

            # Adding clients for current organisation
            Descendant.objects.create(parent=organisation, child=new_org)

            user_ids = UserProfile.objects.values_list('id', flat=True)
            filtered_organisation_user = sys.maxint
            created_user = None
            while filtered_organisation_user != 0:
                created_user = UserProfile.objects.get(
                    pk=random.choice(user_ids))
                filtered_organisation_user = OrganisationUser.objects.filter(profile=created_user,
                                                                             organisation=organisation).count()

            OrganisationUser.objects.create(organisation=organisation,
                                            profile=created_user, access=random.choice(access))

        # generating project list
        for _ in range(0, rows):
            org_ids = Organisation.objects.values_list('id', flat=True)
            client = Organisation.objects.get(pk=random.choice(org_ids))
            if client.id != organisation.id:
                Project.objects.create(organisation=organisation, client=client,
                                       title=fake.sentence(
                                           nb_words=4, variable_nb_words=True),
                                       description=fake.paragraph(nb_sentences=3, variable_nb_sentences=True))

        return u'Test data generated successfully'
