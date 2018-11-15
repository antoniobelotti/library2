from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template

from xhtml2pdf import pisa

from library_services.models import Shelf, Copy


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

def create_copies(book, use_destination, number_of_copies):
    print("create copies", book, number_of_copies)
    for shelf in Shelf.objects.all():
        while not shelf.is_full() and number_of_copies > 0:
            Copy(
                book=book,
                on_shelf=shelf,
                use_destination=use_destination
            ).save()

            number_of_copies -= 1

        if number_of_copies == 0:
            return
