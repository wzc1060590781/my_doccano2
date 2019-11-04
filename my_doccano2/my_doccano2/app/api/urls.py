from django.conf.urls import url
from rest_framework_jwt.views import obtain_jwt_token
from . import views

urlpatterns = [
    url(r'^users/$', views.UserView.as_view({'get': 'list', 'post': 'create'})),
    url(r'^users/(?P<pk>\d+)$',
        views.UserView.as_view({'get': 'retrieve', 'put': 'update', "patch": "update", 'delete': 'destroy'})),
    url(r'^authorizations/$', obtain_jwt_token),
    url(r'^projects/$', views.ProjectView.as_view({'get': 'list', 'post': 'create'})),
    url(r'^projects/(?P<pk>\d+)$',
        views.ProjectView.as_view({'get': 'retrieve', 'put': 'update', "patch": "update", 'delete': 'destroy'})),
    url(r'^projects/(?P<project_id>\d+)/docs$', views.DocView.as_view({'get': 'list', 'post': 'create'})),
    url(r'^projects/(?P<project_id>\d+)/docs/(?P<pk>\d+)$',
        views.DocView.as_view({'get': 'retrieve', 'delete': 'destroy'})),
    url(r'^projects/(?P<project_id>\d+)/labels$', views.LabelView.as_view({'get': 'list', 'post': 'create'})),
    url(r'^projects/(?P<project_id>\d+)/labels/(?P<pk>\d+)$',
        views.LabelView.as_view({'get': 'retrieve', 'put': 'update', "patch": "update", 'delete': 'destroy'})),
    url(r'^projects/(?P<project_id>\d+)/docs/(?P<doc_id>\d+)/annotations$',
        views.AnnotationView.as_view({'get': 'list', 'post': 'create'})),
    url(r'^projects/(?P<project_id>\d+)/docs/(?P<doc_id>\d+)/annotations/(?P<pk>\d+)$',
        views.AnnotationView.as_view({'get': 'retrieve', 'delete': 'destroy'})),
    url(r'^projects/(?P<project_id>\d+)/statistics$', views.StatisticView.as_view()),
    url(r"^project_user_relations/$",
        views.ProjectUserView.as_view({'get': 'list', 'post': 'create'})),
    url(r"^project_user_relations/(?P<pk>\d+)$",
        views.ProjectUserView.as_view({'get': 'retrieve', 'put': 'update', "patch": "update", 'delete': 'destroy'})),
    url(r"^users/(?P<pk>\d+)/password",
        views.ChangePasswordView.as_view()),
]
