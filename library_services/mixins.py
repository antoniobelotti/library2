from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy


class StaffUserRequiredMixin(object):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "Permission denied", "danger")
            return HttpResponseRedirect(reverse_lazy("user-profile"))

        return super(StaffUserRequiredMixin, self).dispatch(request, *args, **kwargs)

class CollegeStudentRequiredMixin(object):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_college_student:
            messages.error(request, "Permission denied", "danger")
            return HttpResponseRedirect(reverse_lazy("home"))

        return super(
            CollegeStudentRequiredMixin, self).dispatch(request, *args, **kwargs)


class PageTitleAndIsProfileMixin(object):
    page_title = None
    is_profile = False

    def get_context_data(self, **kwargs):
        context = super(PageTitleAndIsProfileMixin, self).get_context_data(**kwargs)

        if not self.page_title:
            raise ValueError("page title required")

        context['title'] = self.page_title
        context['profile'] = self.is_profile

        return context
