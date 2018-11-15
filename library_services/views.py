import os
from _datetime import datetime

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponseServerError, JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils.html import strip_tags
from django.views import View
from django.views.generic import ListView, DetailView, TemplateView, FormView

from library_services.forms import BuyBookForm, AddBookForm, AddCopiesForm, TurnstileForm
from library_services.mixins import StaffUserRequiredMixin, PageTitleAndIsProfileMixin, CollegeStudentRequiredMixin
from library_services.utils import render_to_pdf, create_copies
from users_accounts.models import Badge
from .models import Book, Loan, QueueOfRentReservations, Copy, ConsultationReservation, StudyHallSeat, \
    StudyHallSeatReservation


class BookListView(PageTitleAndIsProfileMixin, LoginRequiredMixin, ListView):
    template_name = 'books/book_list.html'
    model = Book
    page_title = 'Catalogo'

    def get_queryset(self):
        query_set = self.model.objects.all()
        query = self.request.GET.get('q')
        if query:
            query_set = query_set.filter(
                Q(title__icontains=query) | Q(author__icontains=query))
        return query_set


class BookDetailView(PageTitleAndIsProfileMixin, LoginRequiredMixin, DetailView):
    model = Book
    template_name = 'books/book_detail.html'
    page_title = 'Dettaglio libro'

    def get_context_data(self, **kwargs):
        context = super(BookDetailView, self).get_context_data(**kwargs)
        user = self.request.user
        book = self.object

        context["active_loan"] = Loan.objects.get_active_loan_by_user_and_book(user, book)
        context["has_reservation"] = QueueOfRentReservations.objects.is_user_already_in_queue(user, book)

        return context

    def post(self, request, *args, **kwargs):
        """
            handles request from user regarding a book:
                -insert a loan
                -reserve a loan
                -reserve a consultation copy
        """

        book = self.get_object()
        user = request.user
        action = request.POST.get("action")

        if action == "insert_loan":
            return self.__handle_insert_loan_request(request, book, user)

        elif action == "insert_rent_reservation":
            return self.__handle_insert_rent_reservation(request, book, user)

        elif action == "insert_consultation_reservation":
            return self.__handle_insert_consultation_reservation(request, book, user)

    def __handle_insert_consultation_reservation(self, request, book, user):
        datestr = request.POST.get("date")
        date = datetime.strptime(datestr, "%d/%m/%Y").date()

        if not book.has_consultation_copy_available_on_date(date):  # todo non va
            messages.info(self.request, "Non ci sono copie disponibili per quel giorno", "warning")
            return HttpResponseRedirect(self.request.path_info)

        book_copy = book.get_consultation_copy_for_date(date)
        ConsultationReservation(
            user=user, date=date, copy=book_copy).save()
        messages.success(
            request,
            """ Prenotazione consultazione inserita con successo!
                Riceverai una mail di conferma con tutte le informazioni. """,
            extra_tags="success"
        )

        # email to user
        self.__send_email_to_user(
            "cons_reservation_inserted",
            "Conferma prenotazione consultazione",
            book,
            'cons-reservations',
            date)

        return HttpResponseRedirect(self.request.path)

    def __handle_insert_rent_reservation(self, request, book, user):
        # if user somehow makes a post request but already has an active
        # reservation refresh the page
        if QueueOfRentReservations.objects.is_user_already_in_queue(
                user, book):
            return HttpResponseRedirect(self.request.path_info)

        """can fail if the user is already in queue for the book"""
        res = QueueOfRentReservations.objects.push(user, book)
        if res:

            messages.success(
                request,
                """Prenotazione inserita con successo! Riceverai una mail di conferma con tutte le informazioni.""",
                extra_tags="success")

            # email to user
            self.__send_email_to_user(
                "reservation_inserted",
                "Conferma prenotazione prestito",
                book,
                'rent-reservations')

            return HttpResponseRedirect(self.request.path)

        else:
            return HttpResponseServerError()

    def __handle_insert_loan_request(self, request, book, user):
        if Loan.objects.get_active_loan_by_user_and_book(user, book):
            return HttpResponseRedirect(self.request.path_info)

        # create loan
        book_copy = book.get_rent_copy()
        Loan(
            user=user,
            book_copy=book_copy,
            started_on=None,
            finished_on=None,
            renewed_on=None
        ).save()

        messages.success(
            request,
            """Prestito inserito con successo! Riceverai una mail di conferma con tutte le informazioni.""",
            extra_tags="success")

        # email to user
        self.__send_email_to_user(
            "loan_inserted",
            "Conferma disponibilità prestito",
            book,
            'active-loans')

        return HttpResponseRedirect(self.request.path)

    def __send_email_to_user(self, template_name, email_subject, book, redirect, date=None):

        """ sends email to logged in user using html template"""
        ctx = {
            'date': datetime.now().date(),
            'user': "{} {}".format(self.request.user.first_name, self.request.user.last_name),
            'book': "{} - {}".format(book.title, book.author),
            'profile_url': self.request.build_absolute_uri(reverse(redirect)),
            'cons_res_date': date
        }

        html_content = render_to_string(
            'users/emails/{}.html'.format(template_name), ctx)
        # Strip the html tag. So people can see the pure text at least.
        text_content = strip_tags(html_content)

        msg = EmailMultiAlternatives(
            email_subject, text_content, "biblioteca.universitaria@unimi.it", [
                self.request.user.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()


class BookStaffDetailView(StaffUserRequiredMixin, FormView, DetailView):
    model = Book
    template_name = 'staff/book_detail.html'
    form_class = AddCopiesForm

    def get_context_data(self, **kwargs):
        context = super(BookStaffDetailView, self).get_context_data(**kwargs)
        copies = Copy.objects.filter(book=self.object.id).select_related()
        data = []
        for copy in copies:
            data.append({
                "copy": copy,
                "active_loan": Loan.objects.get_active_loan_by_copy(copy),
                "disable_actions": (
                        copy.has_active_loan()
                        or copy.has_cons_reservation()
                        or copy.has_rent_reservation()
                        )
            })

        context['data'] = data
        context['title'] = 'Dettaglio'

        return context

    def form_valid(self, form):

        # force form validation ? seems that form_valid doesn't work properly becouse view inherits from detailview
        form.is_valid()

        num_rent_copies = form.cleaned_data["number_of_rent_copies"]
        num_cons_copies = form.cleaned_data["number_of_cons_copies"]

        if num_rent_copies > 0:
            create_copies(self.get_object(), Copy.TO_RENT, num_rent_copies)
            messages.success(
                self.request,
                "Copie destinate al noleggio inserite con successo",
                "success")
        if num_cons_copies > 0:
            create_copies(self.get_object(), Copy.TO_CONSULT, num_cons_copies)
            messages.success(
                self.request,
                "Copie destinate alla consultazione inserite con successo",
                "success")
        if num_cons_copies + num_rent_copies == 0:
            messages.error(self.request, "Nessuna copia da inserire", "danger")

        return HttpResponseRedirect(self.request.path)

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        copy_id = request.POST.get("copy_id")

        if action == "form_valid":
            self.form_valid(AddCopiesForm(request.POST))

        elif action == "delete":
            Copy.objects.get(id=copy_id).delete()
            messages.success(
                self.request,
                "Copia rimossa con successo",
                "warning")

        elif action == "switch_use_destination":
            Copy.objects.get(id=copy_id).switch_use_destination()
            messages.success(
                self.request,
                "Destinazione di utilizzo cambiata con successo",
                "success")

        return HttpResponseRedirect(self.request.path)


class WithdrawView(LoginRequiredMixin, TemplateView):
    template_name = 'withdraw.html'

    def get_context_data(self, **kwargs):
        context = super(WithdrawView, self).get_context_data()

        context["loans_to_withdraw"] = Loan.objects.filter(
            user=self.request.user, started_on=None, finished_on=None).select_related()

        context["cons_reservations"] = \
            [cons for cons in ConsultationReservation.objects.filter(
            user=self.request.user, date=datetime.now().date()).select_related() if not cons.user_is_using_the_copy]

        try:
            context["is_user_inside_study_hall"] = StudyHallSeatReservation.objects.get(
                user=self.request.user, date=datetime.now().date()).is_user_inside_study_hall
        except:
            context["is_user_inside_study_hall"] = None

        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "loan":
            loan = Loan.objects.get(id=request.POST.get("loan_id"))
            loan.started_on = datetime.now().date()
            loan.save()
            return HttpResponseRedirect("book/{}".format(loan.book_copy.book.id))
        elif action == "cons":
            cons_res = ConsultationReservation.objects.get(id=request.POST.get("cons_res_id"))
            cons_res.user_is_using_the_copy = True
            cons_res.save()
            return HttpResponseRedirect("book/{}".format(cons_res.copy.book.id))


class ReturnView(LoginRequiredMixin, TemplateView):
    template_name = 'return.html'

    def get_context_data(self, **kwargs):
        context = super(ReturnView, self).get_context_data(**kwargs)

        context["loans_to_return"] = \
            [loan for loan in Loan.objects.filter(user=self.request.user).select_related() if loan.is_active]

        context["cons_to_return"] = \
            [cons for cons in ConsultationReservation.objects.filter(user=self.request.user, date=datetime.now().date())
             if cons.user_is_using_the_copy]

        return context

    def post(self, request, *args, **kwargs):

        action = request.POST.get("action")
        id=request.POST.get("id")

        if action == "loan":
            loan = Loan.objects.get(id=id)

            if loan.started_on is None:
                loan.delete()
            else:
                loan.finished_on = datetime.now().date()
                loan.save()

            return HttpResponseRedirect("book/{}".format(loan.book_copy.book.id))
        if action == "cons":
            cons = ConsultationReservation.objects.get(id=id)
            cons.user_is_using_the_copy=False
            cons.save()
            return HttpResponseRedirect("book/{}".format(cons.copy.book.id))


class DaysBookIsNotAvailableForConsView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        book_id = kwargs['pk']
        copy_set = Book.objects.get(id=book_id).copy_set.all()
        to_consult_copies = copy_set.filter(use_destination=Copy.TO_CONSULT)
        all_reservations = None

        for copy in to_consult_copies:
            all_reservations = ConsultationReservation.objects.filter(
                copy=copy)
        if all_reservations is None:
            all_reservations = {}

        res = list()
        for reservation in all_reservations:
            res.append(reservation.date.strftime("%m/%d/%Y"))

        return JsonResponse(res, safe=False)


class LibrarianView(PageTitleAndIsProfileMixin, StaffUserRequiredMixin, TemplateView):
    template_name = 'staff/librarian-admin-panel.html'
    page_title = 'Pannello amminstrazione'
    is_profile = True


class ToWithdrawBookListView(PageTitleAndIsProfileMixin, StaffUserRequiredMixin, TemplateView):
    template_name = 'staff/books-waiting-withdraw.html'
    page_title = 'Libri da preparare'
    is_profile = True

    # returns loans waiting for withdraw
    def get_context_data(self, **kwargs):
        context = super(ToWithdrawBookListView, self).get_context_data()
        loans = [loan for loan in Loan.objects.all() if not loan.is_started()]
        ready = []
        not_ready = []

        for loan in loans:
            copy = Copy.objects.get(id=loan.book_copy.id)
            dict_data = {
                'loan_id': loan.id,
                'loan_ready_for_withdraw': loan.ready_for_withdraw,
                'user_email': loan.user,
                'isbn': copy.book.isbn,
                'title': copy.book.title,
                'author': copy.book.author,
                'copy_id': copy.id,
                'shelf_id': copy.on_shelf.id,
                'shelf_pos': copy.on_shelf.position
            }

            if dict_data['loan_ready_for_withdraw']:
                ready.append(dict_data)
            else:
                not_ready.append(dict_data)

        context['to_prepare'] = not_ready
        context['ready_to_withdraw'] = ready

        return context

    def post(self, request, *args, **kwargs):
        loan_id = request.POST.get("loan_id")
        loan = Loan.objects.get(id=loan_id)
        loan.ready_for_withdraw = True
        loan.save()

        return HttpResponseRedirect(self.request.path)


class BuyBookView(PageTitleAndIsProfileMixin, StaffUserRequiredMixin, FormView):
    template_name = 'staff/buy-book.html'
    form_class = BuyBookForm
    page_title = 'Richiedi acquisto libro'
    is_profile = True

    def form_valid(self, form):
        messages.success(
            self.request,
            "La richiesta di acquisto per \"{title} - {author}\" è stata inviata al personale addetto"
                .format(title=form.cleaned_data['title'], author=form.cleaned_data['author']),
            extra_tags='success'
        )

        #test
        print("richiesta acquisto ", form.cleaned_data)

        return HttpResponseRedirect(reverse_lazy('librarian-admin-panel'))


class AddBookView(PageTitleAndIsProfileMixin, StaffUserRequiredMixin, FormView):
    form_class = AddBookForm
    template_name = 'staff/add-book-and-copies.html'
    page_title = 'Aggiungi Libro'
    is_profile = True

    def form_valid(self, form):
        book = Book(
            cover_img=form.cleaned_data['cover_img'],
            title=form.cleaned_data['title'],
            author=form.cleaned_data['author'],
            publishing_year=form.cleaned_data['publishing_year'],
            language=form.cleaned_data['language'],
            isbn=form.cleaned_data['isbn'],
        )
        book.save()

        messages.success(self.request, "Libro inserito con successo. "
                                       "Aggiungi il numero di copie disponibili nella pagina dedicata", "success")

        return HttpResponseRedirect(reverse_lazy('book-detail-staff', kwargs={'pk':book.id}))


class SeatReservationView(CollegeStudentRequiredMixin, TemplateView):
    template_name = 'users/seat-reservation.html'

    def get_context_data(self, **kwargs):
        context = super(SeatReservationView, self).get_context_data(**kwargs)

        context['reservations'] = StudyHallSeatReservation.objects.filter(user=self.request.user)

        context['title'] = 'Prenota posto'
        context['profile'] = True

        return context

    def post(self, request, *args, **kwargs):
        res_to_delete_id = request.POST.get("reservation_id")

        if res_to_delete_id:
            StudyHallSeatReservation.objects.get(id=res_to_delete_id).delete()
            messages.success(
                request,
                "Prenotazione rimossa con successo",
                "success")
        else:

            date = datetime.strptime(
                request.POST.get("date"), "%d/%m/%Y").date()

            seat = self.get_available_seat_on(date, request.user)

            if seat:
                StudyHallSeatReservation(
                    user=request.user,
                    seat=seat,
                    date=date
                ).save()
                messages.success(
                    request,
                    "Prenotazione effettuata con successo",
                    "success")
            else:
                messages.error(
                    request,
                    "Non ci sono posti disponibili oppure hai già una prenotazione attiva per quel giorno",
                    "danger")

        return HttpResponseRedirect(reverse_lazy("seat-reservation"))

    def get_available_seat_on(self, date, user):
        seats = StudyHallSeat.objects.all()
        for seat in seats:
            if seat.is_available_on(date):
                if not StudyHallSeatReservation.objects.get_reservation_by_user_date(
                        user=user, date=date):
                    return seat
        return None


class ActiveLoansListView(PageTitleAndIsProfileMixin, LoginRequiredMixin, ListView):
    model = Loan
    template_name = 'users/active_loans.html'
    page_title = 'Prestiti in corso'
    is_profile = True

    def get_queryset(self):
        qs = [loan for loan in Loan.objects.filter(user=self.request.user).select_related() if loan.is_active]
        return qs

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        loan_id = request.POST.get("delete_loan")
        loan = Loan.objects.get(id=loan_id)
        book = loan.book_copy.book

        if action == "delete_loan":
            loan.delete()
            self.__notify_user(
                "success",
                "Prestito rimosso con successo! Riceverai una mail di conferma.",
                "loan_deleted",
                book,
                'loans-history')

        elif action == "renew_loan":
            loan.renewed_on = datetime.now().date()
            loan.finished_on = None
            loan.save()
            self.__notify_user(
                "success",
                "Prestito rinnovato con successo! Riceverai una mail di conferma.",
                "loan_renewed",
                book,
                'active-loans')

        return HttpResponseRedirect(self.request.path)

    def __notify_user(self, result, message, template_name, book, redirect):
        messages.info(
            self.request,
            message,
            extra_tags=result
        )

        ctx = {
            'date': datetime.now().date(),
            'user': "{} {}".format(self.request.user.first_name, self.request.user.last_name),
            'book': "{} - {}".format(book.title, book.author),
            'profile_url': self.request.build_absolute_uri(reverse(redirect)),
        }

        html_content = render_to_string(
            'users/emails/{}.html'.format(template_name), ctx)
        # Strip the html tag. So people can see the pure text at least.
        text_content = strip_tags(html_content)

        msg = EmailMultiAlternatives(
            "Notifica",
            text_content,
            "biblioteca.universitaria@unimi.it",
            [self.request.user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()


class LoansHistoryListView(PageTitleAndIsProfileMixin, LoginRequiredMixin, ListView):
    model = Loan
    template_name = 'users/loans_history.html'
    page_title = 'Storico Prestiti'
    is_profile = True

    def get_queryset(self):
        qs = [loan for loan in Loan.objects.filter(
            user=self.request.user).select_related() if not loan.is_active]
        return qs


class RentReservationsListView(PageTitleAndIsProfileMixin, LoginRequiredMixin, ListView):
    page_title = 'Prenotazioni pestiti'
    is_profile = True
    template_name = 'users/rent_reservations.html'
    model = Loan

    def get_queryset(self):
        qs = QueueOfRentReservations.objects.filter(
            user_id=self.request.user.id).select_related()
        return qs

    def post(self, request, *args, **kwargs):
        res_id = request.POST.get("delete_rent_res")
        QueueOfRentReservations.objects.get(id=res_id).delete()
        messages.success(
            request,
            """Prenotazione rimossa con successo! Riceverai una mail di conferma.""",
            extra_tags="danger")
        email = EmailMessage(
            'Rimozione prestito',
            'La sua richiesta di rimozione del prestito relativo al libro {} è stata soddisfatta.',
            'notifiche@bibliotecauniversitaria.com',
            to=[self.request.user.email],
        )

        try:
            email.send(fail_silently=False)
        except Exception:
            pass  # TODO: handle

        return HttpResponseRedirect(self.request.path)


class ConsultationReservationsListView(PageTitleAndIsProfileMixin, CollegeStudentRequiredMixin, ListView):
    page_title = 'Prenotazioni prestiti in consultazione'
    is_profile = True
    template_name = 'users/cons_reservations.html'
    model = ConsultationReservation

    def get_queryset(self):
        qs = ConsultationReservation.objects.filter(
            user_id=self.request.user.id).select_related()
        return qs

    def post(self, request, *args, **kwargs):
        res_id = request.POST.get("delete_cons_res")
        ConsultationReservation.objects.get(id=res_id).delete()
        messages.success(
            request,
            """Prenotazione rimossa con successo! Riceverai una mail di conferma.""",
            extra_tags="danger")
        # todo: send mail

        return HttpResponseRedirect(self.request.path)


class EnterStudyHallView(CollegeStudentRequiredMixin, FormView):
    template_name = 'enter-study-hall.html'
    form_class = TurnstileForm
    success_url = reverse_lazy('enter-study-hall')

    def get_form_kwargs(self):
        kwargs = super(EnterStudyHallView, self).get_form_kwargs()
        kwargs.update({'submit_button_text': 'Entra in aula studio'})
        return kwargs

    def form_valid(self, form):
        try:
            badge = Badge.objects.get(code=form.cleaned_data['badge_code'])
            res = StudyHallSeatReservation.objects.get(user=get_user_model().objects.get(badge=badge),
                                                       date=datetime.now().date())
        except:
            res = None

        if res and not res.is_user_inside_study_hall:
            messages.info(self.request, "ok puoi entrare in sala studio", "success")
            res.is_user_inside_study_hall = True
            res.save()
        else:
            messages.info(self.request, "Non hai prenotato oppure risulti già dentro la sala studio. Non puoi entrare", "danger")

        return super(EnterStudyHallView, self).form_valid(form)


class ExitStudyHall(CollegeStudentRequiredMixin, FormView):
    template_name = 'exit-study-hall.html'
    form_class = TurnstileForm
    success_url = reverse_lazy('exit-study-hall')

    def get_form_kwargs(self):
        kwargs = super(ExitStudyHall, self).get_form_kwargs()
        kwargs.update({'submit_button_text': 'Esci dalla sala studio'})
        return kwargs

    def form_valid(self, form):
        badge = Badge.objects.get(code=form.cleaned_data['badge_code'])
        user = get_user_model().objects.get(badge=badge)
        if not user.is_using_consultation_copies:
            messages.info(self.request, "ok puoi uscire", "success")
            res = StudyHallSeatReservation.objects.get(date=datetime.now().date(), user=user)
            res.is_user_inside_study_hall = False
            res.save()
        else:
            messages.info(self.request, "non puoi uscire fino a che non restituisci i libri in consultazione", "danger")
        return super(ExitStudyHall, self).form_valid(form)


class GenerateBadge(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):

        image_logo = os.path.join(os.getcwd(), 'static\images', 'favicon_96' + '.png')

        context = {
            'title': 'Badge',
            'user': self.request.user,
            'image': image_logo
        }
        pdf = render_to_pdf('users/badge.html', context)

        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = "badge.pdf"
            content = "attachment; filename='%s'" % (filename)
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Not found")
