from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Creates a librarian'

    def handle(self, *args, **options):

        librarian = get_user_model().objects.create_superuser(
            username='default',
            email='library@unimi.it',
            first_name='biblio',
            last_name='tecario',
            fiscal_code='999999999999999',
            password='admin',
        )
        librarian.save()

        EmailAddress(
            verified= True,
            primary= True,
            user_id=librarian.id,
            email=librarian.email
        ).save()

        self.stdout.write(self.style.SUCCESS('Librarian account created'))