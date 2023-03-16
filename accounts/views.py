from django.urls import reverse_lazy
from django.views.generic import CreateView

from accounts.forms import SignUpForm


# Create your views here.
class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('accounts:login')
    template_name = 'accounts/signup.html'
