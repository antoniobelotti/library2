import copy

from django.db import models


class LoanManager(models.Manager):
    def get_active_loan_by_user_and_book(self, user, book):
        qs = super(LoanManager, self).get_queryset()
        user_loans = qs.filter(user=user)

        active_user_loans = []
        for loan in user_loans:
            if loan.is_active is True:
                active_user_loans.append(loan)

        for loan in active_user_loans:
            if loan.book_copy.book.id == book.id:
                return loan
        return None

    def get_active_loan_by_copy(self, copy):
        qs = super(LoanManager, self).get_queryset()
        loan = [loan for loan in qs.filter(book_copy=copy) if loan.is_active]
        return loan

    def get_active_loans(self):
        qs = super(LoanManager, self).get_queryset()
        return [loan for loan in qs if loan.is_active]


class QueueManager(models.Manager):
    """ custom manager for QueuOfRentReservations.
    pop returns the first user id in the queue (and deletes it from db) or none if queue is empty.
    push insert a user in the queue
    """

    def pop(self, book):
        qs = super(QueueManager, self).get_queryset()

        book_qs = qs.filter(book=book)
        first_reservation_in_queue = book_qs.order_by('id').first()

        if first_reservation_in_queue:
            res = copy.deepcopy(first_reservation_in_queue)
            first_reservation_in_queue.delete()
            return res

    def push(self, user, book):
        qs = super(QueueManager, self).get_queryset()
        if qs.all().filter(user=user, book=book):
            return None
        qs.create(user=user, book=book)
        return True

    def is_user_already_in_queue(self, user, book):
        qs = super(QueueManager, self).get_queryset()

        res = qs.filter(book=book).filter(user=user).first()

        return False if res is None else True


class StudyHallSeatReservationManager(models.Manager):
    def get_reservation_by_user_date(self, user, date):
        qs = super(StudyHallSeatReservationManager, self).get_queryset()
        return qs.filter(user=user, date=date)
