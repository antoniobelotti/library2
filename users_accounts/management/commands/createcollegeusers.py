from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Creates some college users_accounts'

    def handle(self, *args, **options):
        john= get_user_model().objects.create_user(
            username='default',
            email='john.wick@studenti.unimi.it',
            first_name='john',
            last_name='wick',
            fiscal_code='1111111111111111',
            registration_number='111111',
            password='unimi'
        )
        john.save()

        EmailAddress(
            verified=True,
            primary=True,
            user_id=john.id,
            email=john.email
        ).save()

        tony = get_user_model().objects.create_user(
            username='default',
            email='tony.stark@studenti.unimi.it',
            first_name='tony',
            last_name='stark',
            fiscal_code='2222222222222222',
            registration_number='222222',
            password='unimi'
        )
        tony.save()
        EmailAddress(
            verified=True,
            primary=True,
            user_id=tony.id,
            email=tony.email
        ).save()

        luke = get_user_model().objects.create_user(
            username='default',
            email='luke.skywalker@studenti.unimi.it',
            first_name='luke',
            last_name='skywalker',
            fiscal_code='3333333333333333',
            registration_number='333333',
            password='unimi'
        )
        luke.save()
        EmailAddress(
            verified=True,
            primary=True,
            user_id=luke.id,
            email=luke.email
        ).save()

        self.stdout.write(self.style.SUCCESS('College students accounts created'))