import django_filters

from api.models import User, Project, ProjectUser


class UserFilter(django_filters.rest_framework.FilterSet):
    project = django_filters.CharFilter(method='project_filter', label="project")

    def project_filter(self, queryset, name, value):
        project = Project.objects.filter(name=value)
        if len(project) == 0:
            return project
        return project[0].users.all()

    class Meta:
        model = User
        fields = ("project","username")