# -*- coding: utf-8 -*-

import logging

from django.contrib.auth.models import BaseUserManager
from django.utils import timezone

from .enums import PersonGroupType

logger = logging.getLogger(__name__)


class PersonManager(BaseUserManager):

    def _create_user(self, id, password, is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given id and password.
        """
        # import the organization factory here to avoid cyclic import error
        now = timezone.now()
        user = self.model(
            # the username field is not the PK or id
            pk=id,
            is_staff=is_staff,
            is_active=True,
            is_superuser=is_superuser,
            last_login=now,
            person_group=PersonGroupType.SYSTEM_ADMIN,
            # just create a fake organization using faker
            # as the organization is needed for signals to be executed
            # organization=OrganizationFactory(),
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, id, password=None, **extra_fields):
        return self._create_user(id, password, False, False, **extra_fields)

    def create_superuser(self, id, password, **extra_fields):
        """creates a superuser in the system

        Arguments:
            id or PK of the user
            password of the user

        Returns:
            Newly created user object
        """
        return self._create_user(id, password, True, True, **extra_fields)
