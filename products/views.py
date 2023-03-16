from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import (BooleanField, Case, DecimalField, Exists, F,
                              OuterRef, Q, Subquery, Value, When)
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView, View)

from products.mixins import IsStaffMixin

from .models import PriceRecord, Product

# Create your views here.


def order_to_model(order):
    if order == 'price':
        return 'latest_price'
    elif order == '-price':
        return '-latest_price'
    elif order == 'updated':
        return '-last_update_at'
    elif order == '-updated':
        return 'last_update_at'
    elif order == 'name' or order == '-name':
        return order
    return None


class ListProductsView(ListView):
    model = Product
    context_object_name = 'products'
    paginate_by = 20
    ordering = ['-pk']

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related('prices')

        # filter by following or not
        following = self.request.GET.get('following', None)
        if following is not None and self.request.user.is_authenticated:
            if following == '1':
                queryset = queryset.filter(followers__in=[self.request.user])
            elif following == '0':
                queryset = queryset.exclude(followers__in=[self.request.user])

        # search by name
        if self.request.GET.get('q'):
            queryset = queryset.filter(
                name__icontains=self.request.GET.get('q'))
        subquery = PriceRecord.objects\
            .filter(product=OuterRef('pk'))\
            .order_by('-registered_at')\
            .values_list('price', flat=True)[:2]

        queryset = queryset.annotate(
            latest_price=Subquery(subquery[:1]),
            # show latest price
            last_update_at=Subquery(
                subquery.values_list('registered_at', flat=True)[:1]),
            previous_price=Subquery(subquery[1:]),
            # show latest price change
            price_diff=Case(
                When(
                    Q(previous_price__isnull=False),
                    then=F('latest_price')-F('previous_price')
                ),
                default=None,
                output_field=DecimalField(max_digits=15, decimal_places=2)
            )
        )
        # mark if user is following the product
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(is_following=Exists(
                self.request.user.products_following.filter(id=OuterRef('pk'))))
        else:
            queryset = queryset.annotate(is_following=Value(
                False, output_field=BooleanField()))

        # order by price, name, latest update
        order = order_to_model(self.request.GET.get('order', '').lower())
        if order:
            queryset = queryset.order_by(order)

        return queryset


class ProductDetailView(DetailView):
    model = Product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['prices'] = self.object.prices.all().order_by('-registered_at')
        context['is_following'] = False
        if self.request.user.is_authenticated:
            context['is_following'] = self.object.followers.filter(
                id=self.request.user.id).exists()
        return context


class CreateProductView(LoginRequiredMixin, IsStaffMixin, CreateView):
    model = Product
    fields = ['name', 'url', 'image_url']


class AddPriceView(LoginRequiredMixin, IsStaffMixin, CreateView):
    model = PriceRecord
    fields = ['price']
    product = None

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.product = self.product
        return super().form_valid(form)


class UpdateProductView(LoginRequiredMixin, IsStaffMixin, UpdateView):
    model = Product
    fields = ['name', 'url', 'image_url']


class DeleteProductView(LoginRequiredMixin, IsStaffMixin, DeleteView):
    model = Product
    success_url = reverse_lazy('products:list_products')


class DeletePriceView(LoginRequiredMixin, IsStaffMixin, DeleteView):
    model = PriceRecord
    context_object_name = 'price_record'

    def get_object(self, queryset=None):
        return get_object_or_404(PriceRecord, pk=self.kwargs['pk'], product__pk=self.kwargs['product_pk'])

    def get_success_url(self):
        return self.object.product.get_absolute_url()


class ToggleFollowingView(LoginRequiredMixin, View):

    def is_ajax(self):
        print(self.request.META.get('HTTP_X_REQUESTED_WITH'))
        return self.request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

    def post(self, request, *args, **kwargs):
        product = get_object_or_404(Product, pk=self.kwargs['pk'])
        if product.followers.filter(id=request.user.id).exists():
            product.followers.remove(request.user)
        else:
            product.followers.add(request.user)
        if self.is_ajax():
            return JsonResponse({'is_following': product.followers.filter(id=request.user.id).exists()})
        return redirect('products:list_products')
