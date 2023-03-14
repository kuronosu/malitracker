from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import (BooleanField, Case, DecimalField, Exists, F,
                              OuterRef, Q, Subquery, Value, When)
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, View

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


def following_to_model(following):
    if following == '1':
        return True
    elif following == '0':
        return False
    return None


class ListProductsView(ListView):
    model = Product
    context_object_name = 'products'
    paginate_by = 10
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
