from django.urls import path
from django.views.generic import RedirectView

from .views import *

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='book-list'), name='home'),
    path('books', BookListView.as_view(), name='book-list'),
    path('book/<int:pk>', BookDetailView.as_view(), name='book-detail'),
    path('book/<int:pk>/days_this_book_is_not_available_for_cons', DaysBookIsNotAvailableForConsView.as_view()),

    path('withdraw', WithdrawView.as_view(), name='withdraw'),
    path('return', ReturnView.as_view(), name='withdraw'),
    path('enter', EnterStudyHallView.as_view(), name='enter-study-hall'),
    path('exit', ExitStudyHall.as_view(), name='exit-study-hall'),

    path('staff', LibrarianView.as_view(), name="librarian-admin-panel"),
    path('to-withdraw-book-list', ToWithdrawBookListView.as_view(), name="to-withdraw-book-list"),
    path('buy-book', BuyBookView.as_view(), name='buy-book'),
    path('add-book-and-copies', AddBookView.as_view(), name='add-book-and-copies'),
    path('book/<int:pk>/staff', BookStaffDetailView.as_view(), name='book-detail-staff'),

    path('profile/active-loans/', ActiveLoansListView.as_view(), name='active-loans'),
    path('profile/loans-history/', LoansHistoryListView.as_view(), name='loans-history'),
    path('profile/rent-reservations/', RentReservationsListView.as_view(), name='rent-reservations'),
    path('profile/cons-reservations/', ConsultationReservationsListView.as_view(), name='cons-reservations'),
    path('profile/seat-reservation/', SeatReservationView.as_view(), name="seat-reservation"),
    path('profile/download-badge', GenerateBadge.as_view(), name='download-badge'),
]
