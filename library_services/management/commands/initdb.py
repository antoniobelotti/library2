from subprocess import call

from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Insert seats in database.'

    def handle(self, *args, **options):
        call(["python", "manage.py", "createseats"])
        call(["python", "manage.py", "inserttestdata"])
        call(["python", "manage.py", "createcollegeusers"])
        call(["python", "manage.py", "createlibrarian"])

        self.stdout.write(self.style.SUCCESS('Done!'))