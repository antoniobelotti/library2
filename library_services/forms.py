from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.forms import ModelForm, IntegerField, Form, CharField

from library_services.models import Book


class BuyBookForm(ModelForm):
    number_of_copies = IntegerField(min_value=1, max_value=10, label="Numero copie richieste")

    class Meta:
        model = Book
        fields = [
            'title',
            'author',
            'publishing_year',
            'language',
            'number_of_copies'
        ]
        labels = {
            # todo use translator ugettext
            'title': 'Titolo',
            'author': 'Autore',
            'publishing_year': 'Anno di Pubblicazione',
            'language': 'Lingua',
            'number_of_copies': 'Numero copie richieste'
        }


class AddCopiesForm(Form):
    number_of_rent_copies = IntegerField(
        min_value=0,
        label='Numero copie destinate al prestito',
        required=True,
        initial=0
    )
    number_of_cons_copies = IntegerField(
        min_value=0,
        label='Numero copie destinate alla consultazione',
        required=True,
        initial=0
    )

    class Meta:
        fields = '__all__'
        labels = {
            'number_of_rent_copies': 'Numero copie destinate al prestito',
            'number_of_cons_copies': 'Numero copie destinate alla consultazione'}


class AddBookForm(ModelForm):

    class Meta:
        model = Book
        fields = [
            'cover_img',
            'title',
            'author',
            'publishing_year',
            'language',
            'isbn'
        ]
        labels = {
            # todo use translator ugettext
            'cover_img': 'Url immagine di copertina',
            'title': 'Titolo',
            'author': 'Autore',
            'publishing_year': 'Anno di Pubblicazione',
            'language': 'Lingua',
            'isbn': 'Codice ISBN',
        }


class TurnstileForm(Form):
    badge_code = CharField(min_length=6, label="Codice badge")

    def __init__(self, *args, **kwargs):
        text = kwargs.pop('submit_button_text')

        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', text, css_class='btn-outline-primary float-right'))
        self.helper.form_method = 'POST'

        super(TurnstileForm, self).__init__(*args, **kwargs)