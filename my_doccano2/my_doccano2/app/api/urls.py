from django.conf.urls import url

from . import views
urlpatterns = [
    url(r'^users/$', views.UserListCreateView.as_view()),
    url(r'^users/(?P<pk>\d+)/$', views.UserRetrieveUpdateDestroyView.as_view()),
    url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),
    url(r'^login/$', views.LoginView.as_view()),
    url(r'^projects/$', views.ProjectView.as_view()),
    url(r'^projects/(?P<pk>\d+)/$', views.ProjectCreateUpdateDestoryView.as_view()),
    url(r'^projects/(?P<project_id>\d+)/docs/$', views.DocCreateListView.as_view()),
    # url(r'^projects/(?P<project_id>\d+)/docs/$', views.DocCreateListView.as_view()),
    url(r'^projects/(?P<project_id>\d+)/docs/(?P<pk>\d+)/$', views.DocGetDeleteView.as_view()),
    url(r'^projects/(?P<project_id>\d+)/labels/$', views.LabelCreateListView.as_view()),
    url(r'^projects/(?P<project_id>\d+)/labels/(?P<pk>\d+)/$', views.LabelGetDeleteView.as_view()),
    url(r'^projects/(?P<project_id>\d+)/docs/(?P<doc_id>\d+)/annotations/$', views.AnnotationCreateListView.as_view()),
    url(r'^projects/(?P<project_id>\d+)/docs/(?P<doc_id>\d+)/annotations/(?P<pk>\d+)/$', views.AnnotationDeleteView.as_view()),
    url(r'^projects/(?P<project_id>\d+)/statistics/$', views.StatisticView.as_view())
]




