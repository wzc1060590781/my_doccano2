from django.contrib.auth import authenticate
from django.shortcuts import render, get_object_or_404

from rest_framework import request, mixins, status
from rest_framework.generics import CreateAPIView, GenericAPIView, ListAPIView, UpdateAPIView, DestroyAPIView, \
    RetrieveAPIView, ListCreateAPIView

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from app.utils.Viewset import ApiModelViewSet
from .models import User, Project, Document
from . import serializers


class UsernameCountView(APIView):
    def get(self, request, username):
        """
        获取指定用户名数量
        """
        count = User.objects.filter(username=username).count()

        response_data = {
            "status": 200,
            "data": {
                'username': username,
                'count': count
            }
        }
        return Response(response_data)


class UserView(ApiModelViewSet):
    serializer_class = serializers.CreateUserSerializer
    queryset = User.objects.all()


class LoginView(GenericAPIView):
    def get(self, request, *args, **kwargs):
        return Response({"message": "欢迎进入登录页面"})

    def post(self, request, *args, **kwargs):
        username = request.data["username"]
        password = request.data["password"]
        user = authenticate(username=username, password=password)
        if user:
            return Response({"id": user.id, "username": user.username})
        # TODO
        return Response({"message": "用户名或密码错误"})


# url(r'^projects/(?P<pk>\d+)/$', views.ProjectListView.as_view()),
# 创建项目，项目列表
class ProjectView(ApiModelViewSet):
    serializer_class = serializers.ProjectSerializer
    queryset = Project.objects.all()

    def get(self, request, pk, *args, **kwargs):
        response = super().get(request, pk, *args, **kwargs)
        response.data["count"] = Project.objects.get(pk=pk).documents.all().count()
        return response


# projects/(?P<project_id>\d+)/docs/
# 上传文件和查看文件列表
class DocView(ApiModelViewSet):
    serializer_class = serializers.DocumentSerializer
    filter_fields = ("is_annoteated",)
    ordering_fields = ('-id')

    def get_queryset(self):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        return project.documents.all().filter(is_delete=False)

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
    serializer_class = serializers.LabelSerializer

    def get_queryset(self):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        return project.labels.all()

    def post(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AnnotationView(ApiModelViewSet):
    serializer_class = serializers.AnnotationSerializer

    def get_queryset(self):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        document = get_object_or_404(Document, pk=self.kwargs["doc_id"])
        return document.annotations.all()

    def post(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        document = get_object_or_404(Document, pk=self.kwargs["doc_id"])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        if len(instance.document.annotations.all()) == 1:
            instance.document.is_annoteated = False
            instance.document.save()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
