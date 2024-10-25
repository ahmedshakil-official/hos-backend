from django.db.models import Q
from common.enums import Status
from core.enums import PersonGroupType
from .models import Person
from .utils import parse_int


class OmisAuthenticator(object):
    """Custom Omis User Authenticator class. This class
    logs in using any of pk, code, email and username of an active user

    Arguments:
        object

    Returns:
        Authenticator class
    """

    supports_object_permissions = True
    supports_anonymous_user = False
    supports_inactive_user = False

    def get_user(self, user_id):
        """this function is for getting a single user by pk

        Arguments:
            user_id {integer}

        Returns:
            User object
        """
        return Person.objects.only(
            'id',
            'first_name',
            'last_name',
            'phone',
            'email',
            'alias',
            'is_superuser',
            'organization',
            'is_staff',
            'password',
            'person_group',
            'status',
            'is_active',
        ).get(pk=user_id)


    def authenticate(self, request, username=None, password=None, phone=None, id=None, email=None):
        """this function is basically used when anyone tries to login

        Arguments:
            username {string or integer} -- username field
            password {string} -- the password of the user
            phone {string} -- kept the phone field to avoid test case issues

        Returns:
            User object -- if success else returns None
        """

        # if phone field is passed treat it as username
        if phone:
            username = phone
        elif id:
            username = id
        elif email:
            username = email

        # if phone and username are not passed
        if not username or not password:
            return None

        try:
            # define how we want to query the database
            user = Person.objects.only(
                'id',
                'first_name',
                'last_name',
                'phone',
                'email',
                'alias',
                'is_superuser',
                'organization',
                'is_staff',
                'password',
                'person_group',
                'status',
            ).get(
                # parse the string to integer else error will be thrown for pk
                # Q(pk=parse_int(username)) |
                # Q(code=username) |
                Q(email=username) |
                Q(phone=username),
                status=Status.ACTIVE,
                person_group__in=[
                    PersonGroupType.SYSTEM_ADMIN,
                    PersonGroupType.EMPLOYEE,
                    PersonGroupType.MONITOR,
                    PersonGroupType.TRADER,
                    PersonGroupType.CONTRACTOR,
                ]
            )
        except Person.DoesNotExist:
            # Try to login adding or removing 0 with phone
            if username[0] == '0':
                username = username[1:]
            else:
                username = ''.join(('0', username))
            try:
                # define how we want to query the database
                user = Person.objects.get(
                    # parse the string to integer else error will be thrown for pk
                    # Q(pk=parse_int(username)) |
                    # Q(code=username) |
                    Q(email=username) |
                    Q(phone=username),
                    status=Status.ACTIVE,
                    person_group__in=[
                        PersonGroupType.SYSTEM_ADMIN,
                        PersonGroupType.EMPLOYEE,
                        PersonGroupType.MONITOR,
                        PersonGroupType.TRADER,
                        PersonGroupType.CONTRACTOR,
                    ]
                )
            except Person.DoesNotExist:
                return None

        return user if user.check_password(password) else None
