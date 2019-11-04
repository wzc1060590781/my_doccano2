from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission

from .models import Project, ProjectUser, User, Label, Document

CHANGE_METHODS = ("PUT", "PATCH")
ADD_AND_DELETE_METHODS = ("DELETE", "POST")
SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')


class ProjectOperationPermission(BasePermission):

    def has_permission(self, request, view):
        user_id = request.user.id
        project_id = view.kwargs.get('pk') or request.query_params.get('project_id')
        if request.user.is_superuser:
            return True
        if project_id:
            project = get_object_or_404(Project, pk=project_id)
            if request.user in project.users.all():
                if request.method in SAFE_METHODS:
                    return True
                if ProjectUser.objects.get(
                        project_id=project_id,
                        user_id=user_id).role == "project_owner" and request.method in CHANGE_METHODS:
                    return True
                else:
                    return False
            else:
                return False
        else:
            if request.method in SAFE_METHODS:
                return True
            else:
                return False


class UserOperationPermission(BasePermission):
    def has_permission(self, request, view):
        opereated_user_id = view.kwargs.get('pk') or request.query_params.get('user_id')
        opereated_user = get_object_or_404(User, pk=opereated_user_id)
        if request.method in SAFE_METHODS:
            return True
        if opereated_user.is_superuser:
            return False
        user_id = request.user.id
        if request.user.is_superuser:
            return True
        if request.method in CHANGE_METHODS:
            if str(user_id) == opereated_user_id:
                return True
            else:
                return False
        else:
            return False


class DocumentOperationPermission(BasePermission):
    """
    项目管理员可添加删除文本
    """

    def has_permission(self, request, view):
        user_id = request.user.id
        self.user_id = user_id
        project_id = view.kwargs.get('project_id') or request.query_params.get('project_id')
        # document_id = view.kwargs.get('pk') or view.kwargs.get('doc_id') or request.query_params.get('doc_id')
        if request.method in CHANGE_METHODS:
            return False
        if request.method in SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        project = get_object_or_404(Project, pk=project_id)
        if request.user in project.users.all() and ProjectUser.objects.get(
                project_id=project_id, user_id=user_id).role == "project_owner":
            return True
        else:
            return False


class LabelOperationPermission(BasePermission):
    def has_permission(self, request, view):
        user_id = request.user.id
        self.user_id = user_id
        if request.user.is_superuser:
            return True
        project_id = view.kwargs.get('project_id') or request.query_params.get('project_id')
        project = get_object_or_404(Project, pk=project_id)
        if request.user in project.users.all():
            if request.method in CHANGE_METHODS:
                if ProjectUser.objects.get(project_id=project_id, user_id=user_id).role == "project_owner":
                    return True
                return False
            elif request.method in SAFE_METHODS:
                return True
            else:
                return False
        else:
            return False


# TODO
class AnnotationOperationPermission(BasePermission):
    def has_permission(self, request, view):
        user_id = request.user.id
        self.user_id = user_id
        project_id = view.kwargs.get('project_id') or request.query_params.get('project_id')
        if request.method in CHANGE_METHODS:
            return False
        if request.user.is_superuser:
            return True
        project = get_object_or_404(Project, pk=project_id)
        if request.user in project.users.all():
            return True
        else:
            return False


class ProjectUserPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        if request.method in SAFE_METHODS:
            return True
        if request.method in ADD_AND_DELETE_METHODS:
            for projectuser in ProjectUser.objects.filter(user=request.user.id):
                if projectuser.role == "project_owner":
                    return True
            else:
                return False
        else:
            return False
