import base64
import json
import os
import pickle

from django.contrib.auth.decorators import permission_required
from django.core.mail import send_mail
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
# from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from django_redis import get_redis_connection
from rest_framework import status, mixins
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView, CreateAPIView, UpdateAPIView, RetrieveAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.views import ObtainJSONWebToken

from algorithm.models import Algorithm
from algorithm.serializers import AlgorithmSerializer
from api import constants
from api.serializers import ResetPasswordSerializer, DocumentFromDBSerializer
from app.utils.Viewset import ApiModelViewSet
from app.utils.celery_function import generate_verify_email_url, generate_doc_list
from app.utils.filter import UserFilter
from celery_tasks.algorithm.tasks import train_model
from celery_tasks.email.tasks import send_find_password_email
from .models import User, Project, Document, ProjectUser
from . import serializers
from .permissions import ProjectOperationPermission, DocumentOperationPermission, LabelOperationPermission, \
    AnnotationOperationPermission, ProjectUserPermission, UserOperationPermission, ProjectAlgorithmPermission


class UsernameCountView(APIView):
    """
    用户名数量
    """
    def get(self, request, username):
        """
        获取指定用户名数量
        """
        count = User.objects.filter(username=username).count()
        data = {
            "status":200,
            "message":"请求成功",
            'username': username,
            'count': count
        }
        return Response(data)

class MobileCountView(APIView):
    """
    手机号数量
    """
    def get(self, request, phone_number):
        """
        获取指定手机号数量
        """
        count = User.objects.filter(phone_number=phone_number).count()
        data = {
            "status": 200,
            "message": "请求成功",
            'phone_number': phone_number,
            'count': count
        }
        return Response(data)

class EamilCountView(APIView):
    """
    手机号数量
    """
    def get(self, request, email):
        """
        获取指定手机号数量
        """
        count = User.objects.filter(phone_number=email).count()
        data = {
            "status": 200,
            "message": "请求成功",
            'email': email,
            'count': count
        }
        return Response(data)

class UserAuthorizeView(ObtainJSONWebToken):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 400:
            response = {
                "status": 400,
                "success": False,
                "message": "用户名和密码不匹配",
            }
            return Response(response,status=status.HTTP_400_BAD_REQUEST)
        else:
            return response

class UserView(ApiModelViewSet):
    """
    用户的列表，修改账户信息
    """
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.CreateUserSerializer
    queryset = User.objects.filter(is_delete=False)
    filter_backends = [DjangoFilterBackend]
    filter_class = UserFilter
    filter_fields = ("username","project")

    def get_serializer_class(self):
        if self.action == "update":
            return serializers.UpdateSelfSerializer
        else:
            return serializers.CreateUserSerializer

    def update(self, request, *args, **kwargs):
        if self.kwargs["pk"] == str(request.user.id):
            kwargs["partial"] = True
            return super().update(request, *args, **kwargs)
        else:
            raise PermissionDenied("没有权限修改其他用户信息")

    def destroy(self, request, *args, **kwargs):
        instance = get_object_or_404(User, pk=self.kwargs['pk'])
        if instance.is_superuser or not request.user.is_superuser:
            data = {}
            data["status"] = status.HTTP_403_FORBIDDEN
            data["success"] = False
            data["message"] = "没有删除该用户权限"
            return Response(data,status=status.HTTP_403_FORBIDDEN)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CreateUserView(ApiModelViewSet):
    """注册用户"""
    serializer_class = serializers.CreateUserSerializer


class ChangePasswordView(ApiModelViewSet):
    """修改密码"""
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ChangePasswordSerializer

    def create(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=self.kwargs['pk'])
        if user.id == request.user.id:
            return super().create(request, *args, **kwargs)
        else:
            raise PermissionDenied("没有权限修改其他用户密码")


# url(r'^projects/(?P<pk>\d+)/$', views.ProjectListView.as_view()),
# 创建项目，项目列表
class ProjectView(ApiModelViewSet):
    serializer_class = serializers.ProjectSerializer
    permission_classes = [IsAuthenticated, ProjectOperationPermission]
    filter_fields = ("project_type",)

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Project.objects.all()
        return user.project_set.all()

    def get(self, request, pk, *args, **kwargs):
        response = super().get(request, pk, *args, **kwargs)
        response.data["count"] = Project.objects.get(pk=pk).documents.all().count()
        return response

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


# projects/(?P<project_id>\d+)/docs/
# 上传文件和查看文件列表
class DocView(ApiModelViewSet):
    """
    文本增删改查视图
    """
    permission_classes = [IsAuthenticated, DocumentOperationPermission]
    filter_fields = ("is_annoteated",)
    ordering_fields = ('id')

    def get_serializer_class(self):
        if self.action == "post" and self.request.data["is_multitext"]:
            return serializers.DocumentSerializer
        else:
            return serializers.CreateMultiDocument

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
    def create(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.data["is_multitext"]:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            data = serializer.save()
            doc_list = data["doc_list"]
            wrong_count = data["wrong_count"]
            right_count = len(doc_list)
            document_list = []
            for doc in doc_list:
                doc_dict = {}
                doc_dict["id"] = doc.id
                doc_dict["project"] = doc.project.name
                doc_dict["is_annoteated"] = False
                doc_dict["text"] = doc.text
                doc_dict["title"] = doc.title
                document_list.append(doc_dict)
            response_data = {}
            response_data["wrong_count"] = wrong_count
            response_data["right_count"] = right_count
            response_data["doc_list"] = document_list
            if right_count == 0:
                status_code = status.HTTP_400_BAD_REQUEST
                response_data["success"] = False
                response_data["message"] = "未上传成功任何文件"
            else:
                status_code = status.HTTP_201_CREATED
                response_data["success"] = True
                response_data["message"] = "成功"
            response_data["status"] = status_code
            return Response(response_data, status=status_code)


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

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request,*args,**kwargs)


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


# class AlgorithmView(ApiModelViewSet):
#     def get_serializer_class(self):
#         if self.action == "update":
#             return serializers.UpdateAlgorithmSerializer
#         else:
#             return serializers.AlgorithmSerializer
#
#     def get_queryset(self):
#         if self.request.user.is_superuser:
#             return Algorithm.objects.filter(is_delete=False)
#         else:
#             raise PermissionDenied("权限不足")


class SendEmail(GenericAPIView):
    def post(self, request):
        email = request.data["email"]
        user = get_object_or_404(User, email=email)
        user_id = user.id
        verify_url = generate_verify_email_url(user_id, email)
        send_find_password_email.delay(email, verify_url)
        return Response(
            {
                "status": 200,
                "success": True,
                "message": "发送成功"
            }, status=status.HTTP_200_OK)

class VerifyToken(GenericAPIView):
    def post(self,request):
        token = request.data["token"]
        if not token:
            response_data = {
                "status":400,
                "success":False,
                "message":"缺少token"
            }
        else:
            user = User.check_verify_email_token(token)
            if user:
                response_data = {
                    "status": 200,
                    "success": True,
                    "message": "验证成功",
                    "data":{
                        "id":user.id,
                        "email":user.email,
                        "token":token
                    }
                }
            else:
                response_data = {
                    "status": 400,
                    "success": False,
                    "message": "token有误或已过期"
                }
        return Response(response_data,status=response_data["status"])

class ResetPassword(UpdateAPIView):
    serializer_class = ResetPasswordSerializer

    # def get_queryset(self):
    #     return User.objects.all()

    #  TODO
    def put(self, request, *args, **kwargs):
        token = request.data.get('token')
        if not token:
            return Response({'message': '缺少token'}, status=status.HTTP_400_BAD_REQUEST)
        user_id = request.data.get("id", None)
        instance = User.objects.get(pk=user_id)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_data={}
        response_data["status"] = 200
        response_data["success"] = True
        response_data["message"] = "修改成功"
        response_data["data"] = serializer.data
        return Response(response_data,status=status.HTTP_200_OK)

class DocumentOperatingHistoryView(CreateAPIView):
    """
    用户操作历史记录
    """
    serializer_class = serializers.AddDocumentOperatingHistorySerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.user.id
        redis_conn = get_redis_connection('history')
        dict_list = []
        doc_list = redis_conn.lrange('history_list_%s' % user_id,0,-1)
        for doc_id in doc_list:
            user_hash = redis_conn.hget('history_%s' % user_id,doc_id)
            value = pickle.loads(base64.b64decode(user_hash))
            doc = Document.objects.get(pk=doc_id)
            if not doc:
                continue
            project = doc.project
            doc_dict = {}
            doc_dict["doc_id"] = doc_id
            doc_dict["datetime"] = value["datetime"]
            doc_dict["operation"] = value["operation"]
            doc_dict["title"] = doc.title
            doc_dict["project_name"] = project.name
            doc_dict["project_url"] = "projects/" + str(project.id)
            doc_dict["doc_url"] = "/projects/" + str(project.id) + "/doc/" + str(doc.id)
            dict_list.append(doc_dict)
        serializer = serializers.AddDocumentOperatingHistorySerializer(dict_list, many=True)
        dict = {}
        dict["code"] = status.HTTP_200_OK
        dict["success"] = True
        dict["message"] = "成功"
        dict["data"] = serializer.data
        return Response(dict, status=status.HTTP_200_OK)


    def create(self, request, *args, **kwargs):
        response = super().create(request,*args,**kwargs)
        resp = {}
        resp["code"] = status.HTTP_201_CREATED
        resp["success"] = True
        resp["message"] = "添加成功"
        resp["data"] = response.data
        return Response(resp,status=status.HTTP_201_CREATED)


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

class ChoseAlgorithmView(ListAPIView):
    serializer_class = AlgorithmSerializer
    permission_classes = [ProjectAlgorithmPermission]
    def get_queryset(self):
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project,pk=project_id)
        return Algorithm.objects.filter(algorithm_type=project.project_type)

class TrainModelView(APIView):
    def post(self,request,*args,**kwargs):
        algorithm_id = request.data.get("algorithm_id")
        if not algorithm_id:
            return Response(
                {
                    "status" : status.HTTP_400_BAD_REQUEST,
                    "message":"缺少参数",
                    "success":False
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        algorithm = get_object_or_404(Algorithm,pk=algorithm_id)
        if not algorithm:
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "不存在该算法",
                    "success": False
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        project_id = self.kwargs["project_id"]
        project = get_object_or_404(Project,pk=project_id)
        if project.project_type != algorithm.algorithm_type:
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "算法和项目不匹配",
                    "success": False
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        # if project.documents.filter(is_annoteated=True).count()< algorithm.mini_quantity:
        #     return Response(
        #         {
        #             "status": status.HTTP_400_BAD_REQUEST,
        #             "message": "打标文件未达到算法最低要求",
        #             "success": False
        #         },
        #         status=status.HTTP_400_BAD_REQUEST
        #     )
        # TODO
        doc_list = generate_doc_list(project_id)
        config_name = str(project_id)+"_"+str(algorithm_id)+".json"
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"common_static/configs/"+config_name)
        with open(config_path,"w",encoding="utf8") as f:
            json.dump(doc_list,f,ensure_ascii=False,indent=2)
        algorithm_path = algorithm.algorithm_file.path
        train_model.delay(algorithm_path,config_path)
        return Response(
            {
                "code": 200,
                "message": "正在训练模型",
                "success": True,
            }, status=status.HTTP_200_OK
        )
