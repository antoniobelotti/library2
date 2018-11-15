from datetime import datetime
import random
import string

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from library_services.models import ConsultationReservation


class Badge(models.Model):
    code = models.CharField(max_length=6)


class CustomUser(AbstractUser):
    username = models.CharField(max_length=40, unique=False, default='')

    registration_number = models.CharField(
        _('registration number'),
        max_length=6,
        validators=[MinLengthValidator(limit_value=6)],
        null=True,
        blank=True,
        default=None
    )

    fiscal_code = models.CharField(
        _('codice fiscale'),
        max_length=16,
        validators=[MinLengthValidator(limit_value=16)],
        null=False,
        blank=False,
        unique=True
    )

    badge = models.ForeignKey(Badge, null=True, on_delete=models.SET_NULL)

    @property
    def is_college_student(self):
        return True if self.registration_number is not None else False

    @property
    def is_using_consultation_copies(self):
        if not self.is_college_student:
            return False
        for cons in ConsultationReservation.objects.filter(date=datetime.now().date(), user=self):
            if cons.user_is_using_the_copy:
                return True
        return False


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    """ https://stackoverflow.com/questions/2257441/ """
    return ''.join(random.choice(chars) for _ in range(size))


@receiver(post_save, sender=CustomUser)
def new_user_signup(sender, instance, **kwargs):

    if instance.badge is None:
        badge = Badge(code=id_generator())
        badge.save()
        instance.badge = badge
        instance.save()
