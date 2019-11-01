import random

from django.contrib.auth import authenticate
from django.contrib.auth.views import PasswordResetView
from django.db import transaction
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.shortcuts import render, get_object_or_404, redirect

from rest_framework import request, mixins, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import CreateAPIView, GenericAPIView, ListAPIView, UpdateAPIView, DestroyAPIView, \
    RetrieveAPIView, ListCreateAPIView
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from app.utils.Viewset import ApiModelViewSet

from .models import User, Project, Document, ProjectUser, Annotation
from . import serializers
from .permissions import ProjectOperationPermission, DocumentOperationPermission, UserOperationPermission, \
    LabelOperationPermission, AnnotationOperationPermission, ProjectUserPermission


class UserView(ApiModelViewSet):
    """
    list:
    返回用户列表
    """
    permission_classes = [IsAuthenticated, UserOperationPermission]

    queryset = User.objects.filter(is_delete=False)

    def get_serializer_class(self):
        if self.action == "update":
            if self.kwargs["pk"] == str(self.request.user.id):
                return serializers.UpdateSelfSerializer
            return serializers.UpdateOtherUserSerializer
        else:
            return serializers.CreateUserSerializer

    def destroy(self, request, *args, **kwargs):
        instance = get_object_or_404(User, pk=self.kwargs['pk'])
        print(instance.is_superuser)
        if instance.is_superuser:
            raise PermissionDenied("不可删除超级管理员")
        elif instance.system_role == "system_manager" and not request.user.is_superuser:
            raise PermissionDenied("权限不足")
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangePasswordView(CreateModelMixin, GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ChangePasswordSerializer


# class LoginView(GenericAPIView):
#     # def get(self, request, *args, **kwargs):
#     #     return Response({"message": "欢迎进入登录页面"})
#
#     def post(self, request, *args, **kwargs):
#         try:
#             username = request.data["username"]
#         except:
#             return Response({"message": "请求失败", "status": status.HTTP_400_BAD_REQUEST, "success": False},
#                             status=status.HTTP_400_BAD_REQUEST)
#         try:
#             password = request.data["password"]
#         except:
#             return Response({"message": "请求失败", "status": status.HTTP_400_BAD_REQUEST, "success": False},
#                             status=status.HTTP_400_BAD_REQUEST)
#         user = authenticate(username=username, password=password)
#         if user:
#             print("登录成功")
#             return Response({"id": user.id, "username": user.username, "message": "请求成功", "status": status.HTTP_200_OK,
#                              "success": True})
#         # TODO
#         return Response({"message": "请求失败", "status": status.HTTP_400_BAD_REQUEST, "success": False},
#                         status=status.HTTP_400_BAD_REQUEST)


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

    def get(self, request, pk, *args, **kwargs):
        response = super().get(request, pk, *args, **kwargs)
        response.data["count"] = Project.objects.get(pk=pk).documents.all().count()
        return response


# projects/(?P<project_id>\d+)/docs/
# 上传文件和查看文件列表
class DocView(ApiModelViewSet):
    permission_classes = [IsAuthenticated, DocumentOperationPermission]
    serializer_class = serializers.DocumentSerializer
    filter_fields = ("is_annoteated",)
    ordering_fields = ('-id')

    def get_queryset(self):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        if project in self.request.user.project_set.all():
            qs = project.documents.all().filter(is_delete=False)
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
            while True:
                instance = self.get_object()
                instance.delete()
                try:
                    result = Document.objects.filter(pk=instance.document.id, annotations=None).update(
                        is_annoteated=False)
                    if result:
                        return Response(status=status.HTTP_204_NO_CONTENT)
                    else:
                        transaction.rollback(save_id)
                        continue
                except AttributeError:
                    return Response(status=status.HTTP_204_NO_CONTENT)
                # except:
                #     transaction.rollback(save_id)


class ProjectUserView(ApiModelViewSet):
    serializer_class = serializers.ProjectUserSerializer
    queryset = ProjectUser.objects.all()
    permission_classes = [IsAuthenticated, ProjectUserPermission]

    def destroy(self, request, *args, **kwargs):
        instance = get_object_or_404(ProjectUser, pk=self.kwargs['pk'])
        if request.user.is_superuser or request.user.system_role == "system_manager":
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        elif instance.role == "project_owner":
            raise PermissionDenied("没有删除project_owner权限")


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


class MyException(ModelViewSet):
    def create(self, request, *args, **kwargs):
        return Response({"message": "路径错误", "success": False, "status": 404})

    def retrieve(self, request, *args, **kwargs):
        return Response({"message": "路径错误", "success": False, "status": 404})

    def update(self, request, *args, **kwargs):
        return Response({"message": "路径错误", "success": False, "status": 404})

    def destroy(self, request, *args, **kwargs):
        return Response({"message": "路径错误", "success": False, "status": 404})
