from django.urls import reverse_lazy
from allauth.account.views import SignupView, PasswordChangeView

from .forms import CustomUserCreationForm


class SignUpViewCustom(SignupView):
    form_class = CustomUserCreationForm
    template_name = 'account/signup.html'


class PasswordChangeViewCustom(PasswordChangeView):

    @property
    def success_url(self):
        return reverse_lazy('account_login')

    def get_context_data(self, **kwargs):
        context = super(PasswordChangeViewCustom, self).get_context_data(**kwargs)

        context['title'] = 'Cambia password'
        context['profile'] = True

        return context


