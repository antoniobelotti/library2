from library_services.models import StudyHallSeat
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Insert seats in database.'

    def handle(self, *args, **options):
        for i in range(0, 50):
            StudyHallSeat().save()
        self.stdout.write(self.style.SUCCESS('Seats created'))
