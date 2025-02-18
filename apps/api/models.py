from tastypie.resources import ModelResource

from apps.cryptocurrency_wi.models import CriptoCoin, CoinInfo


class CriptoCoinResource(ModelResource):
    class Meta:
        queryset = CriptoCoin.objects.all()
        resource_name = 'criptocoin'
        allowed_methods = ['get']


class CoinInfoResource(ModelResource):
    class Meta:
        queryset = CoinInfo.objects.all()
        resource_name = 'coininfo'
        allowed_methods = ['get', 'post', 'delete']

