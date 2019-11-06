from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView, CreateAPIView
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from app.utils.Viewset import ApiModelViewSet
from .models import User, Project, Document, ProjectUser, Algorithm
from . import serializers
from .permissions import ProjectOperationPermission, DocumentOperationPermission, UserOperationPermission, \
    LabelOperationPermission, AnnotationOperationPermission, ProjectUserPermission


class UserView(ApiModelViewSet):
    """
    list:
    返回用户列表
    """
    # permission_classes = [IsAuthenticated, UserOperationPermission]
    serializer_class = serializers.CreateUserSerializer
    queryset = User.objects.filter(is_delete=False)
    filter_fields = ("username",)

    def get_serializer_class(self):
        if self.action == "update":
            return serializers.UpdateSelfSerializer
        else:
            return serializers.CreateUserSerializer

    def destroy(self, request, *args, **kwargs):
        instance = get_object_or_404(User, pk=self.kwargs['pk'])
        if instance.is_superuser:
            raise PermissionDenied("不可删除超级管理员")
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CreateUserView(ApiModelViewSet):
    serializer_class = serializers.CreateUserSerializer



class ChangePasswordView(ApiModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ChangePasswordSerializer

    def create(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=self.kwargs['pk'])
        if user.id == request.user.id:
            return super().create(request,*args,**kwargs)
        else:
            raise PermissionDenied("没有权限修改其他用户密码")


# url(r'^projects/(?P<pk>\d+)/$', views.ProjectListView.as_view()),
# 创建项目，项目列表
class ProjectView(ApiModelViewSet):
    serializer_class = serializers.ProjectSerializer
    permission_classes = [IsAuthenticated, ProjectOperationPermission]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Project.objects.all()
        return user.project_set.all()

        # return Project.objects.all()

    def get(self, request, pk, *args, **kwargs):
        response = super().get(request, pk, *args, **kwargs)
        response.data["count"] = Project.objects.get(pk=pk).documents.all().count()
        return response


# projects/(?P<project_id>\d+)/docs/
# 上传文件和查看文件列表
class DocView(ApiModelViewSet):
    """
    文本增删改查视图
    """
    permission_classes = [IsAuthenticated,DocumentOperationPermission]
    serializer_class = serializers.DocumentSerializer
    filter_fields = ("is_annoteated",)
    ordering_fields = ('id')

    def get_queryset(self):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        if project in self.request.user.project_set.all() or self.request.user.is_superuser:
            qs = project.documents.all().filter(is_delete=False)
            if project.randomize_document_order:
                return qs.order_by("?")
            else:
                return qs
        else:
            raise PermissionDenied

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        document_list = []

        for data in response.data["results"]:
            # 一个document
            docuemnt_dict = {}
            docuemnt_dict["id"] = data["id"]
            docuemnt_dict["text"] = data["text"]
            docuemnt_dict["labels"] = []
            annotations = data["annotations"]
            for annotation in annotations:
                per_label_list = []
                label_text = annotation["label"]["text"]
                label_start_offset, label_end_offset = annotation["start_offset"], annotation["end_offset"]
                per_label_list.append(label_start_offset)
                per_label_list.append(label_end_offset)
                per_label_list.append(label_text)
                docuemnt_dict["labels"].append(per_label_list)
            document_list.append(docuemnt_dict)
        response.data = document_list
        return response

    # TODO
    def post(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LabelView(ApiModelViewSet):
    permission_classes = [IsAuthenticated, LabelOperationPermission]
    serializer_class = serializers.LabelSerializer

    def get_queryset(self):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        if project in self.request.user.project_set.all() or self.request.user.is_superuser:
            return project.labels.all()
        else:
            raise PermissionDenied

    def create(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AnnotationView(ApiModelViewSet):
    serializer_class = serializers.AnnotationSerializer
    permission_classes = [IsAuthenticated, AnnotationOperationPermission]

    def get_queryset(self):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        document = get_object_or_404(Document, pk=self.kwargs["doc_id"])
        if self.request.user.is_superuser:
            return document.annotations.all()
        if project in self.request.user.project_set.all() and document in project.documents.all():
            return document.annotations.all()
        else:
            raise PermissionDenied

    def post(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        document = get_object_or_404(Document, pk=self.kwargs["doc_id"])
        if document not in project.documents.all():
            raise Http404
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        document_id = self.kwargs["doc_id"]
        document = get_object_or_404(Document, pk=document_id)
        with transaction.atomic():
            save_id = transaction.savepoint()
            response = Response({
                        "status": status.HTTP_204_NO_CONTENT,
                        "success": True,
                        "message": "成功",
                        "data": None
                    }, status=status.HTTP_204_NO_CONTENT)
            while True:
                # try:
                #     instance = self.get_object()
                #     instance.delete()
                # return Response(status=status.HTTP_204_NO_CONTENT)

                try:
                    instance = self.get_object()
                    instance.delete()
                    result = Document.objects.filter(pk=instance.document.id, annotations=None).update(
                        is_annoteated=False)
                    return response
                except AttributeError:
                    return response
                except Exception:
                    transaction.savepoint_rollback(save_id)
                    continue

class ProjectUserView(ApiModelViewSet):
    permission_classes = [IsAuthenticated, ProjectUserPermission]
    serializer_class = serializers.ProjectUserSerializer
    queryset = ProjectUser.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = get_object_or_404(ProjectUser, pk=self.kwargs['pk'])
        if request.user.is_superuser:
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        elif instance.role == "project_owner":
            raise PermissionDenied("没有删除project_owner权限")
        else:
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class UsersInProjectView(ApiModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.CreateUserSerializer
        elif self.action == "update":
            return serializers.UpdateProjectRoleSerializer
        else:
            return serializers.UsersInProjectSerializer

    def get_queryset(self):
        project = get_object_or_404(Project, pk=self.kwargs["project_id"])
        if self.action == "retrieve":
            return User.objects.all()
        else:
            return ProjectUser.objects.filter(project=project)

    def destroy(self, request, *args, **kwargs):
        user_id = request.user.id
        user = User.objects.get(pk=user_id)
        project_id = self.kwargs["project_id"]
        project = get_object_or_404(Project, pk=project_id)
        operated_user_id = self.kwargs["pk"]
        operated_user = get_object_or_404(User, pk=operated_user_id)
        operated_project_user = ProjectUser.objects.get(project=project, user=operated_user)
        project_user = ProjectUser.objects.get(project=project, user=user)
        operated_project_user.delete()
        if request.user.is_superuser:
            operated_project_user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if project_user.role == "project_owner":
            if operated_project_user.role == "project_owner":
                raise PermissionDenied("没有删除project_owner权限")
            else:
                operated_project_user.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied("权限不足，无法修改项目成员角色")
        operated_user = get_object_or_404(User, pk=self.kwargs["pk"])
        project = get_object_or_404(Project, pk=self.kwargs["project_id"])
        instance = ProjectUser.objects.get(project=project, user=operated_user)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class AlgorithmView(ApiModelViewSet):
    def get_serializer_class(self):
        if self.action == "update":
            return serializers.UpdateAlgorithmSerializer
        else:
            return serializers.AlgorithmSerializer
    def get_queryset(self):
        if self.request.user.is_superuser:
            return Algorithm.objects.filter(is_delete=False)
        else:
            raise PermissionDenied("权限不足")


class StatisticView(APIView):
    def get(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        labels_list = project.labels.all()
        data = {}
        data["label"] = {}
        data["total"] = 0
        for label in labels_list:
            data["label"][label.text] = label.annotations.all().count()
        data["total"] = project.documents.all().count()
        data["remaining"] = project.documents.filter(is_annoteated=False).count()
        return Response(data=data, status=status.HTTP_200_OK)

# class MyException(ModelViewSet):
#     def create(self, request, *args, **kwargs):
#         return Response({"message": "路径错误", "success": False, "status": 404})
#
#     def retrieve(self, request, *args, **kwargs):
#         return Response({"message": "路径错误", "success": False, "status": 404})
#
#     def update(self, request, *args, **kwargs):
#         return Response({"message": "路径错误", "success": False, "status": 404})
#
#     def destroy(self, request, *args, **kwargs):
#         return Response({"message": "路径错误", "success": False, "status": 404})
