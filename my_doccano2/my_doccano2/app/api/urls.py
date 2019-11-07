from django.conf.urls import url
from rest_framework_jwt.views import obtain_jwt_token
from . import views
urlpatterns = [
    url(r'^users/$', views.UserView.as_view({'get': 'list'})),
    url(r'^register/$', views.CreateUserView.as_view({"post":"create"})),
    url(r'^users/(?P<pk>\d+)$',
        views.UserView.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    url(r'^authorizations$', obtain_jwt_token),
    url(r'^projects/$', views.ProjectView.as_view({'get': 'list', 'post': 'create'})),
    url(r'^projects/(?P<pk>\d+)$',
        views.ProjectView.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    url(r'^projects/(?P<project_id>\d+)/docs$', views.DocView.as_view({'get': 'list', 'post': 'create'})),
    url(r'^projects/(?P<project_id>\d+)/docs/(?P<pk>\d+)$',
        views.DocView.as_view({'get': 'retrieve', 'delete': 'destroy'})),
    url(r'^projects/(?P<project_id>\d+)/labels$', views.LabelView.as_view({'get': 'list', 'post': 'create'})),
    url(r'^projects/(?P<project_id>\d+)/labels/(?P<pk>\d+)$',
        views.LabelView.as_view({'get': 'retrieve', 'put': 'update','delete': 'destroy'})),
    url(r'^projects/(?P<project_id>\d+)/docs/(?P<doc_id>\d+)/annotations$',
        views.AnnotationView.as_view({'get': 'list', 'post': 'create'})),
    url(r'^projects/(?P<project_id>\d+)/docs/(?P<doc_id>\d+)/annotations/(?P<pk>\d+)$',
        views.AnnotationView.as_view({'get': 'retrieve', 'delete': 'destroy'})),
    url(r'^projects/(?P<project_id>\d+)/statistics$', views.StatisticView.as_view()),
    url(r'^projects/(?P<project_id>\d+)/users$', views.UsersInProjectView.as_view({'get': "list", "post": "create"})),
    url(r'^projects/(?P<project_id>\d+)/users/(?P<pk>\d+)$',
        views.UsersInProjectView.as_view({"get": "retrieve", 'delete': "destroy", "put": "update"})),
    url(r'^algorithms$', views.AlgorithmView.as_view({'get': "list", "post": "create"})),
    url(r'^algorithms/(?P<pk>\d+)$',
        views.AlgorithmView.as_view({"get": "retrieve", 'delete': "destroy", "put": "update"})),
    url(r"^users/(?P<pk>\d+)/password",
        views.ChangePasswordView.as_view({"post":"create"})),
    url(r"^send_email$",views.SendEmail.as_view()),
    url(r"^reset_password$",views.ResetPassword.as_view()),
]



