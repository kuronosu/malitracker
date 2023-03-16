from django.urls import reverse_lazy
from django.views.generic import CreateView

from accounts.forms import SignUpForm


# Create your views here.
class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('accounts:login')
    template_name = 'accounts/signup.html'

    def post(self, req, *args, **kwargs):
        form = self.get_form()
        form.is_valid()
        print(form.errors)
        return super().post(req, *args, **kwargs)
