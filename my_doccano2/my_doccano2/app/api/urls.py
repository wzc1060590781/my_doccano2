from django.conf.urls import url
from rest_framework_jwt.views import obtain_jwt_token
from . import views
urlpatterns = [
    url(r'^users$', views.UserView.as_view({'get': 'list'})),
    url(r'^register$', views.CreateUserView.as_view({"post":"create"})),
    url(r'^users/(?P<pk>\d+)$',
        views.UserView.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    url(r'^usernames/(?P<username>\w{3,20})/count$', views.UsernameCountView.as_view()),
    url(r'^phone_numbers/(?P<phone_number>1[3-9]\d{9})/count$', views.MobileCountView.as_view()),
    url(r'^emails/(?P<email>[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+)/count$', views.EamilCountView.as_view()),
    url(r'^authorizations$',views.UserAuthorizeView.as_view()),
    url(r'^projects$', views.ProjectView.as_view({'get': 'list', 'post': 'create'})),
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
    url(r"^users/(?P<pk>\d+)/password",
        views.ChangePasswordView.as_view({"post":"create"})),
    url(r"^send_email$",views.SendEmail.as_view()),
    url(r"^reset_password$",views.ResetPassword.as_view()),
    url(r"^verify_token$",views.VerifyToken.as_view()),
    url(r"^operate_historys$",views.DocumentOperatingHistoryView.as_view()),
    url(r"^projects/(?P<project_id>\d+)/algorithms$",views.ChoseAlgorithmView.as_view()),
    url(r"^projects/(?P<project_id>\d+)/train_model",views.TrainModelView.as_view()),
    # url(r"^projects/(?P<project_id>\d+)/users/(?P<user_id>\d+)/tasks", views.TaskView.as_view({'get': "list"})),
    # url(r"^projects_tasks$",views.ProjectTaskView.as_view()),
    # url(r"^projects/(?P<project_id>\d+)/tasks$",views.ProjectTaskView.as_view()),
]



