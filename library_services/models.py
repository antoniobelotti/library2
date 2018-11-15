from datetime import timedelta, datetime

from django.core.validators import RegexValidator
from django.db import models
from django.core.validators import MinLengthValidator
from django.urls import reverse

from library2 import settings
from library_services.managers import StudyHallSeatReservationManager, LoanManager, QueueManager


class Book(models.Model):
    IT = 'it'
    EN = 'en'
    DE = 'de'
    ES = 'es'
    LANGUAGE_CHOICES = (
        ('it', 'Italiano'),
        ('en', 'Inglese'),
        ('de', 'Tedesco'),
        ('es', 'Spagnolo')
    )

    cover_img = models.URLField()
    title = models.CharField(max_length=254)
    author = models.CharField(max_length=254)
    publishing_year = models.CharField(
        validators=[
            RegexValidator(
                r'^[1-2]\d{3,3}$',
                'Not a valid year')],
        max_length=4)
    language = models.CharField(
        null=False,
        choices=LANGUAGE_CHOICES,
        max_length=10)
    isbn = models.CharField(
        max_length=13,
        validators=[
            MinLengthValidator(
                limit_value=10)],
        null=False,
        unique=True)

    _first_available_copy_for_rent = None

    def get_absolute_url(self):
        return reverse('book-detail', args=[str(self.id)])

    def has_at_least_one_rent_copy(self):
        if self.copy_set.filter(use_destination=Copy.TO_RENT).count() > 0:
            return True
        return False

    def has_at_least_one_cons_copy(self):
        if self.copy_set.filter(use_destination=Copy.TO_CONSULT).count() > 0:
            return True
        return False

    def has_copy_available_for_rent(self):
        for copy in self.copy_set.all():
            if copy.is_available_for_rent():
                self._first_available_copy_for_rent = copy
                return True
        return False

    def get_rent_copy(self):
        # first_available_copy is set in has_copy_available
        if self.has_copy_available_for_rent():
            return self._first_available_copy_for_rent

    def has_consultation_copy_available_on_date(self, date):
        for copy in self.copy_set.all():
            if copy.is_available_for_consultation_on(date):
                return True
        return False

    def get_consultation_copy_for_date(self, date):
        for copy in self.copy_set.all():
            if copy.is_available_for_consultation_on(date):
                return copy


class QueueOfRentReservations(models.Model):
    """
    (id, user, book) where id as primary key autoincrement serves as "timestamp".
     """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    objects = QueueManager()


class Shelf(models.Model):
    position = models.CharField(max_length=254)
    capacity = models.IntegerField()

    def is_full(self):
        if self.copy_set.all().count() == self.capacity:
            return True
        return False


class Copy(models.Model):
    TO_CONSULT = 'to_consult'
    TO_RENT = 'to_rent'
    USE_DESTINATIONS = (
        (TO_CONSULT, 'Consultazione in sede'),
        (TO_RENT, 'Destinato al prestito')
    )

    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    on_shelf = models.ForeignKey(Shelf, on_delete=models.SET(None))
    use_destination = models.CharField(
        null=False, choices=USE_DESTINATIONS, max_length=10)

    def is_available_for_rent(self):
        if self.use_destination == self.TO_CONSULT:
            return False

        copy_related_loans = self.loan_set.filter(book_copy=self)
        active_loans = [loan for loan in copy_related_loans if loan.is_active]

        if active_loans.__len__() == 0:
            return True
        return False

    def is_available_for_consultation_on(self, date):
        if self.use_destination == self.TO_RENT:
            return False

        copy_cons_reservation_on_given_date = ConsultationReservation.objects.filter(copy=self).filter(date=date)

        if copy_cons_reservation_on_given_date.count() == 0:
            return True
        return False

    def has_active_loan(self):
        try:
            loan_list = Loan.objects.filter(book_copy=self.id)
        except BaseException:
            loan_list = None

        active_loan = [loan for loan in loan_list if loan.is_active]
        return True if active_loan else False

    def has_rent_reservation(self):
        try:
            reservation = QueueOfRentReservations.objects.get(copy=self.id)
        except BaseException:
            reservation = None

        return True if reservation is not None else False

    def has_cons_reservation(self):
        try:
            rs = ConsultationReservation.objects.filter(copy=self.id)
        except BaseException:
            rs = None

        cons_reservation = [
            res for res in rs if res.date > datetime.now().date()]

        return True if cons_reservation else False

    def switch_use_destination(self):
        if self.use_destination == Copy.TO_CONSULT:
            self.use_destination = Copy.TO_RENT
        else:
            self.use_destination = Copy.TO_CONSULT

        self.save()


class ConsultationReservation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(null=False)
    copy = models.ForeignKey(Copy, on_delete=models.CASCADE)
    user_is_using_the_copy = models.BooleanField(default=False)


class Loan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book_copy = models.ForeignKey(Copy, on_delete=models.CASCADE)
    inserted_on = models.DateField()

    started_on = models.DateField(null=True)
    finished_on = models.DateField(null=True)
    renewed_on = models.DateField(null=True)

    ready_for_withdraw = models.BooleanField(default=False)

    objects = LoanManager()

    @property
    def is_expired(self):

        if (
                self.is_started() and
                self.expiration_date() < datetime.now().date() and
                self.finished_on is None
        ):
            return True

        return False

    @property
    def is_active(self):
        return True if self.finished_on is None else False

    def is_expired_by(self):
        """returns the number of days the loan has expired or none instead"""

        if self.is_expired is False:
            return None

        delta = datetime.now().date() - self.started_on

        return delta.days - 30

    def is_started(self):
        return False if self.started_on is None else True

    @property
    def can_be_renewed(self):
        if not self.is_expired:
            return False

        if self.is_expired_by() < 5:
            return True
        else:
            return False

    def has_been_renewed(self):
        return True if not self.renewed_on else False

    def expiration_date(self):
        if self.started_on is None:
            return None
        if self.has_been_renewed():
            return self.started_on + timedelta(days=60)
        else:
            return self.started_on + timedelta(days=30)

    @property
    def completed(self):
        if self.finished_on is not None:
            return True

    def save(self, *args, **kwargs):
        if self.inserted_on is None:
            self.inserted_on = datetime.now().date()
        super(Loan, self).save(*args, **kwargs)


class StudyHallSeat(models.Model):

    def is_available_on(self, date):
        if StudyHallSeatReservation.objects.filter(
                seat=self.id, date=date).count() == 0:
            return True
        return False


class StudyHallSeatReservation(models.Model):
    seat = models.ForeignKey(StudyHallSeat, on_delete=models.CASCADE)
    date = models.DateField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_user_inside_study_hall = models.BooleanField(default=False)

    objects = StudyHallSeatReservationManager()

    # can't have multi-attribute primary key
    class Meta:
        unique_together = (("seat", "date", "user"),)


