from django.contrib.auth import get_user_model
from django.core.management import BaseCommand
from library_services.models import Book, Copy, Shelf, Loan

from datetime import  datetime


class Command(BaseCommand):
    help = 'Insert some test data in database. Requires some users_accounts already in db'

    def handle(self, *args, **options):

        book_1 = Book(
            cover_img='http://bookcoverarchive.com/wp-content/uploads/amazon/1984.jpg',
            title='1984',
            author='George Orwell',
            publishing_year=1948,
            language=Book.IT,
            isbn='9788804668237'
        )

        book_2 = Book(
            cover_img='https://upload.wikimedia.org/wikipedia/en/thumb/9/9b/LordOfTheFliesBookCover.jpg/220px-LordOfTheFliesBookCover.jpg',
            title='The lord of flies',
            author='Willian Golding',
            publishing_year=1954,
            language=Book.EN,
            isbn='9788804663065'
        )

        book_3 = Book(
            cover_img='https://static.lafeltrinelli.it/static/frontside/xxl/639/3942639_251036.jpg',
            title='Norwegan wood',
            author='Haruki Murakami',
            publishing_year=1987,
            language=Book.IT,
            isbn='9788806216467'
        )

        book_4 = Book(
            cover_img='https://images-na.ssl-images-amazon.com/images/I/51JRbLm4kGL._SX323_BO1,204,203,200_.jpg',
            title = 'Guida galattica per gli autostoppisti',
            author = 'Douglas Adams',
            publishing_year = 1980,
            language =Book.IT,
            isbn ='9788804666851'

        )

        book_5 = Book(
            cover_img='http://api2.edizpiemme.it/uploads/2017/10/978886836615HIG_409a798a3d5e804dee73e0f7a84343ad.JPG',
            title='Il poeta',
            author='Michael Connelly',
            publishing_year=1996,
            language=Book.IT,
            isbn='9780759507852'
        )

        shelf_1 = Shelf(position="piano terra - sezione proibita", capacity=75)

        book_1.save()
        book_2.save()
        book_3.save()
        book_4.save()
        book_5.save()

        shelf_1.save()

        copy1 = Copy(
            book = book_1,
            on_shelf=shelf_1,
            use_destination=Copy.TO_RENT
        )

        copy2 =Copy(
            book=book_1,
            on_shelf=shelf_1,
            use_destination=Copy.TO_RENT
        )

        copy3 =Copy(
            book=book_1,
            on_shelf=shelf_1,
            use_destination=Copy.TO_CONSULT
        )

        copy4 = Copy(
            book=book_2,
            on_shelf=shelf_1,
            use_destination=Copy.TO_RENT
        )

        copy5 =Copy(
            book=book_3,
            on_shelf=shelf_1,
            use_destination=Copy.TO_RENT
        )

        copy6 =Copy(
            book=book_3,
            on_shelf=shelf_1,
            use_destination=Copy.TO_RENT
        )

        copy7 = Copy(
            book=book_4,
            on_shelf=shelf_1,
            use_destination=Copy.TO_RENT
        )

        copy8 = Copy(
            book=book_4,
            on_shelf=shelf_1,
            use_destination=Copy.TO_CONSULT
        )

        copy9 = Copy(
            book=book_5,
            on_shelf=shelf_1,
            use_destination=Copy.TO_RENT
        )

        copy1.save()
        copy2.save()
        copy3.save()
        copy4.save()
        copy5.save()
        copy6.save()
        copy7.save()
        copy8.save()
        copy9.save()

        self.stdout.write(self.style.SUCCESS('Books and copies created'))
