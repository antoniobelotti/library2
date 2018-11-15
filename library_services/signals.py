import django.dispatch
from django.core.mail import EmailMessage
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from library_services.models import Loan, QueueOfRentReservations, Copy, Shelf


loan_ended = django.dispatch.Signal(providing_args=["loan"])


@receiver(post_save, sender=Loan)
def notify_book_loan_has_ended(sender, instance, **kwargs):
    if instance.completed:
        loan_ended.send(sender=Loan, loan=instance)


@receiver(loan_ended, sender=Loan)
def loan_ended_handler(sender, loan, **kwargs):
    book = loan.book_copy.book
    book_copy=loan.book_copy
    first_res_in_queue_for_book = QueueOfRentReservations.objects.pop(book)

    if first_res_in_queue_for_book:
        loan = Loan(
            user=first_res_in_queue_for_book.user,
            book_copy=book_copy,
            started_on=None,
            finished_on=None,
            renewed_on=None
        )

        # todo make email prettier
        email = EmailMessage(
            'Notifica disponibilità prestito',
            'La informiamo che il libro da lei prenotato è disponibile al ritiro entro 7 giorni',
            'notifiche@bibliotecauniversitaria.com',
            to=[first_res_in_queue_for_book.user.email],
        )

        try:
            email.send(fail_silently=False)
        except Exception:
            print("errore") # TODO: handle

        loan.save()


@receiver(pre_save, sender=Copy)
def update_shelf_capacity(sender, instance, **kwargs):
    """ decrement capacity of shelf when a copy is assigned to the shelf """
    shelf = Shelf.objects.get(id=instance.on_shelf.id)

    if instance in shelf.copy_set.all():
        return
    else:
        shelf.capacity -=1
        shelf.save()