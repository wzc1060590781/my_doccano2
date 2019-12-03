from django.conf.urls import url

from algorithm import views

urlpatterns = [
    url(r'^algorithms$', views.AlgorithmView.as_view({'get': 'list',"post":"create"})),
    url(r'^algorithms/(?P<pk>\d+)$', views.AlgorithmView.as_view({"put":"update"})),
]