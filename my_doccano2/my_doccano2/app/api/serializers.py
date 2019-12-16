import base64
import datetime
import json
import os
import pickle
import re
import time

from django.contrib.auth.hashers import check_password

from django.db import transaction
from django.db.models import Q
from django_redis import get_redis_connection

from rest_framework import serializers
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework_jwt.settings import api_settings

from api import constants
from app import settings
from app.utils.upload_text_utils import val_text_name, get_text_str, val_text_format
from .models import User, Project, ProjectUser, Document, Label, Annotation, Task


class UpdateSelfSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', "phone_number", "email")
        extra_kwargs = {
            'username': {
                'min_length': 3,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许3-20个字符的用户名',
                    'max_length': '仅允许3-20个字符的用户名',
                }
            }
        }

    def validate_phone_number(self, value):
        """验证手机号"""
        print("*****************")
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value


class ResetPasswordSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    username = serializers.CharField(read_only=True)
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(read_only=True)
    token = serializers.CharField(write_only=True)
    email = serializers.CharField()

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password2', "phone_number", "token", "email")

    def validate(self, attrs):
        token = attrs["token"]
        user = User.check_verify_email_token(token)
        if user:
            if user.id != attrs["id"]:
                raise serializers.ValidationError("token和用户信息不匹配")
            if attrs['password'] != attrs['password2']:
                raise serializers.ValidationError('两次密码不一致')
            else:
                return attrs
        else:
            raise serializers.ValidationError("token有误")

    def update(self, instance, validated_data):
        instance.set_password(validated_data["password"])
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.ModelSerializer):
    username = serializers.CharField(read_only=True)
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(read_only=True)
    origin_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password2', "origin_password", "phone_number")
        extra_kwargs = {
            'new_password': {
                'write_only': True,
                'min_length': 6,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许6-20个字符的密码',
                    'max_length': '仅允许6-20个字符的密码',
                }
            }
        }

    def validate(self, data):
        user = self.context["request"].user
        if not check_password(data["origin_password"], user.password):
            raise serializers.ValidationError("密码错误")
        # 判断两次密码
        if data['password'] != data['password2']:
            raise serializers.ValidationError('两次密码不一致')
        return data

    def create(self, validated_data):
        del validated_data["origin_password"]
        del validated_data["password2"]
        # password = validated_data["password"]
        user_id = self.context["request"].user.id
        user = User.objects.get(pk=user_id)
        user.set_password(validated_data["password"])
        user.save()
        return user


class LabelSerializer(serializers.ModelSerializer):
    project = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Label
        fields = ["id", "text", "background_color", "project", "prefix_key", "suffix_key"]
        extra_kwargs = {
            'background_color': {
                'min_length': 7,
                'max_length': 7,
                'error_messages': {
                    'min_length': '颜色长度必须为7',
                    'max_length': '颜色长度必须为7',
                }
            }
        }

    def validate_text_color(self, value):
        if not value.startswith("#"):
            raise serializers.ValidationError("颜色字符串应以#开始")
        for i in value[1:]:
            if i not in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f"]:
                raise serializers.ValidationError("颜色输入有误，所包含字符必须在[0-9,a-f]内")
        return value

    def validate_background_color(self, value):
        try:
            value = self.validate_text_color(value)
        except serializers.ValidationError as e:
            raise e
        return value

    def validate(self, attrs):
        text = attrs["text"]
        background_color = attrs["background_color"]
        project_id = self.context["view"].kwargs["project_id"]
        project = Project.objects.get(pk=int(project_id))
        attrs["project"] = project
        labels_queryset = Label.objects.filter(project_id=project_id).filter(
            Q(text=text) | Q(background_color=background_color))
        pk = self.context["view"].kwargs.get("pk")
        exsist_count = labels_queryset.count()
        if exsist_count == 0:
            return attrs
        elif exsist_count == 1:
            if pk and pk == str(labels_queryset[0].id):
                return attrs
            else:
                raise serializers.ValidationError("项目中已存在该标签或已存在该颜色标签")
        else:
            raise serializers.ValidationError("项目中已存在该标签或已存在该颜色标签")


class SubLabelSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    text = serializers.CharField(read_only=True)
    background_color = serializers.CharField(read_only=True)
    class Meta:
        model = Label
        fields = ["id", "text","background_color"]


class AnnotationSerializer(serializers.ModelSerializer):
    prob = serializers.DecimalField(max_digits=4, decimal_places=3, max_value=1.0, min_value=0.0, read_only=True)
    manual = serializers.BooleanField(read_only=True)
    label = SubLabelSerializer(read_only=True)
    label_id = serializers.IntegerField(write_only=True)
    annoted_by = serializers.CharField(read_only=True)
    document = serializers.CharField(read_only=True)

    class Meta:
        model = Annotation
        fields = ["id", "document", "prob", "manual", "label", "start_offset", "end_offset", "annoted_by", "label_id"]

    def validate(self, attrs):
        start_offset = attrs["start_offset"]
        end_offset = attrs["end_offset"]
        try:
            start_offset = int(start_offset)
            end_offset = int(end_offset)
        except Exception:
            raise serializers.ValidationError("标签的开始下标和结束下标应该为整数")
        if start_offset < 0 or end_offset < 0:
            raise serializers.ValidationError("开始或结束下标不得小于0")
        if start_offset >= end_offset:
            raise serializers.ValidationError("开始下标应小于结束下标")
        document_id = self.context["view"].kwargs["doc_id"]
        document = Document.objects.get(pk=int(document_id))
        if end_offset > len(document.text):
            raise serializers.ValidationError("结束下标不得超出文本长度")
        for annotation in document.annotations.all():
            if start_offset == annotation.start_offset or start_offset == annotation.end_offset or end_offset == annotation.start_offset or end_offset == annotation.end_offset:
                raise  serializers.ValidationError("开始下标或结束下标与已打标签重合")
            if start_offset > annotation.start_offset and start_offset < annotation.end_offset:
                raise serializers.ValidationError("开始下标与已打标签重合")
            elif end_offset > annotation.start_offset and end_offset < annotation.end_offset:
                raise serializers.ValidationError("结束下标与已打标签重合")
            elif start_offset < annotation.start_offset and end_offset>annotation.end_offset:
                raise serializers.ValidationError("标签包含已打标签")
        attrs["document"] = document
        return attrs

    def create(self, validated_data):
        document_id = validated_data["document"].id
        document = get_object_or_404(Document, pk=document_id)
        with transaction.atomic():
            save_id = transaction.savepoint()
            while True:
                label_id = validated_data["label_id"]
                label = get_object_or_404(Label, pk=int(label_id))
                start_offset = validated_data["start_offset"]
                end_offset = validated_data["end_offset"]
                annoted_by = self.context["request"].user
                annotation = Annotation.objects.filter(start_offset=start_offset, end_offset=end_offset,
                                                       document=document).first()
                if annotation:
                    try:
                        annotation.delete()
                        annotation = Annotation.objects.create(start_offset=start_offset, end_offset=end_offset,
                                                               document=document, label=label,
                                                               annoted_by=annoted_by, manual=True)
                        annotation.save()
                        Document.objects.filter(pk=annotation.document.id).update(
                            is_annoteated=True)
                        document.save()
                        return annotation
                    except:
                        transaction.savepoint_rollback(save_id)
                        continue
                else:
                    try:
                        annotation = Annotation.objects.create(start_offset=start_offset, end_offset=end_offset,
                                                               document_id=document.id, label=label,
                                                               annoted_by=annoted_by, manual=True)
                        Document.objects.filter(pk=Annotation.objects.get(pk=annotation.id).document_id).update(
                            is_annoteated=True)
                        return annotation
                    except:
                        transaction.savepoint_rollback(save_id)
                        continue


class DocumentSerializer(serializers.ModelSerializer):
    text_upload = serializers.FileField(write_only=True)
    text = serializers.CharField(read_only=True)
    annotations = AnnotationSerializer(many=True, read_only=True)
    is_annoteated = serializers.BooleanField(default=False)
    title = serializers.CharField(read_only=True)
    is_multitext = serializers.BooleanField(write_only=True, allow_null=False)

    class Meta:
        model = Document
        fields = ('id', "text_upload", "text", 'project', "is_annoteated", "annotations", "title", "is_multitext")

    def validate(self, attrs):
        if not attrs["is_multitext"]:
            text = self.context["request"].FILES.get("text_upload")
            if not text:
                raise serializers.ValidationError('未上传文件')
            try:
                title = val_text_name(text.name)
                attrs["title"] = title
            except:
                raise serializers.ValidationError("文件名有误")
            text_str = get_text_str(text)
            try:
                val_text_format(text, text_str)
            except:
                raise serializers.ValidationError("格式有误")
            if Document.objects.filter(text=text_str).count():
                raise serializers.ValidationError('文件已存在，请勿重复上传')
            attrs["text"] = text_str
            return attrs

    def create(self, validated_data):
        del validated_data["text_upload"]
        del validated_data["is_multitext"]
        project_id = self.context["view"].kwargs["project_id"]
        project = Project.objects.get(pk=int(project_id))
        validated_data["project"] = project
        return super().create(validated_data)


class CreateMultiDocument(serializers.ModelSerializer):
    text_upload = serializers.FileField(write_only=True)
    text = serializers.CharField(read_only=True)
    annotations = AnnotationSerializer(many=True, read_only=True)
    is_annoteated = serializers.BooleanField(default=False)
    title = serializers.CharField(read_only=True)
    is_multitext = serializers.BooleanField(write_only=True, allow_null=False)
    wrong_count = serializers.BooleanField(write_only=True, allow_null=False)

    class Meta:
        model = Document
        fields = (
            'id', "text_upload", "text", 'project', "is_annoteated", "annotations", "title", "wrong_count",
            "is_multitext")

    def validate(self, attrs):
        file_list = self.context["request"].FILES.getlist('text_upload')
        if len(file_list) == 0:
            raise serializers.ValidationError("未上传文件")
        wrong_count = 0
        right_file_list = []
        for text in file_list:
            text_dict = {}
            try:
                title = val_text_name(text.name)
                text_dict["title"] = title
            except:
                # raise serializers.ValidationError("文件名有误")
                wrong_count += 1
                continue
            text_str = get_text_str(text)
            try:
                val_text_format(text, text_str)
            except:
                wrong_count += 1
                continue
            if Document.objects.filter(text=text_str).count():
                wrong_count += 1
                continue
            text_dict["text"] = text_str
            right_file_list.append(text_dict)
        attrs["file_list"] = right_file_list
        attrs["wrong_count"] = wrong_count
        return attrs

    def create(self, validated_data):
        wrong_count = validated_data["wrong_count"]
        file_list = validated_data["file_list"]
        project_id = self.context["view"].kwargs["project_id"]
        project = Project.objects.get(pk=int(project_id))
        data = {}
        doc_list = []
        for file in file_list:
            try:
                doc = Document.objects.create(text=file["text"], project=project, title=file["title"])
                doc_list.append(doc)
            except:
                wrong_count += 1
        data["wrong_count"] = wrong_count
        data["doc_list"] = doc_list
        data["project"] = project.name
        return data


class ProjectSerializer(serializers.ModelSerializer):
    count = serializers.IntegerField(read_only=True)
    pic = serializers.ImageField(required=False)
    update_time = serializers.DateTimeField(read_only=True)
    labels = LabelSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = (
            'id', 'name', "description", "project_type", "randomize_document_order", "update_time", "count",
            "pic", "labels")

    def validate(self, attrs):
        picture = attrs.get("pic", None)
        if picture:
            picture.name = str(int(time.time())) + "." + picture.name.split(".")[1]
            attrs["pic"] = picture
        return attrs


class SubProjectSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)

    class Meta:
        model = Project
        fields = ["id", "name", "description"]


class SubUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "phone_number"]


class ProjectUserSerializer(serializers.ModelSerializer):
    project = SubProjectSerializer(read_only=True)
    project_id = serializers.IntegerField(write_only=True)
    user_id = serializers.IntegerField(write_only=True)
    user = SubUserSerializer(read_only=True)
    role = serializers.CharField()

    class Meta:
        model = ProjectUser
        fields = ("id", 'user', "user_id", "project", "project_id", "role")

    def validate(self, attrs):
        project_id = self.context["view"].kwargs["project_id"] or attrs["project_id"]
        operated_user_id = self.context["view"].kwargs["pk"] or attrs["user_id"]
        role = attrs["role"]
        user = self.context["request"].user
        if user.is_superuser:
            return attrs
        user_id = self.context["request"].user.id
        operated_project_user = ProjectUser.objects.get(project_id=project_id, user_id=operated_user_id)
        project_user = ProjectUser.objects.get(project_id=project_id, user_id=user_id)
        if operated_project_user:
            raise PermissionDenied("该用户存在于该项目")
        if project_user.role == "project_owner" and role == "user":
            return attrs
        else:
            raise PermissionDenied("无操作权限")

    def create(self, validated_data):
        project_id = validated_data["project_id"]
        project = get_object_or_404(Project, pk=project_id)
        operated_user_id = validated_data["user_id"]
        operated_user = get_object_or_404(User, pk=operated_user_id)
        role = validated_data["role"]
        project_user = ProjectUser(project=project, user=operated_user, role=role)
        project_user.save()
        return project_user


#
class UserInMultiProjects(serializers.ModelSerializer):
    """用户所在项目序列化器"""
    project = SubProjectSerializer(read_only=True)

    class Meta:
        model = ProjectUser
        fields = ("id", "project", "project_id", "role")


class CreateUserSerializer(serializers.ModelSerializer):
    """创建用户的序列化器"""
    password2 = serializers.CharField(label='确认密码', write_only=True)
    phone_number = serializers.CharField(label="手机号")
    token = serializers.CharField(label='JWT token', read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    projectuser_set = UserInMultiProjects(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'password', 'password2', "phone_number", "token", "email", "is_superuser",
            "projectuser_set")
        extra_kwargs = {
            'username': {
                'min_length': 3,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许3-20个字符的用户名',
                    'max_length': '仅允许3-20个字符的用户名',
                }
            },
            'password': {
                'write_only': True,
                'min_length': 6,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许6-20个字符的密码',
                    'max_length': '仅允许6-20个字符的密码',
                }
            },
            'phone_number': {
                'min_length': 11,
                'max_length': 11,
                'error_messages': {
                    'min_length': '手机号必须为11位',
                    'max_length': '手机号必须为11位',
                }
            }
        }

    def validate_phone_number(self, value):
        """验证手机号"""
        print("*****************")
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value

    def validate(self, data):
        # 判断两次密码
        if data['password'] != data['password2']:
            raise serializers.ValidationError('两次密码不一致')
        phone_number = data["phone_number"]
        username = data["username"]
        email= data["email"]
        if User.objects.filter(username=username):
            raise serializers.ValidationError('用户名已存在')
        elif User.objects.filter(phone_number=phone_number):
            raise serializers.ValidationError('手机号已存在')
        elif User.objects.filter(email=email):
            raise serializers.ValidationError('邮箱已存在')
        return data

    def create(self, validated_data):
        """重写保存方法，增加密码加密"""
        # 移除数据库模型类中不存在的属性
        del validated_data['password2']
        phone_number = validated_data["phone_number"]
        username = validated_data["username"]
        exsist_user = User.objects.filter(phone_number=phone_number, username=username)
        if exsist_user:
            exsist_user.is_delete = False
            return exsist_user
        user = super().create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        # 签发jwt token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        user.token = token
        return user


class UsersInProjectSerializer(serializers.ModelSerializer):
    user = SubUserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    project = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ProjectUser
        fields = ("user", "role", "project", "user_id")

    def validate(self, attrs):
        user = self.context["request"].user
        user = User.objects.get(pk=user.id)
        project_id = self.context["view"].kwargs["project_id"]
        project = get_object_or_404(Project, pk=project_id)
        operated_user_id = attrs["user_id"]
        operated_user = get_object_or_404(User, pk=operated_user_id)
        role = attrs["role"]
        attrs["project"] = project
        attrs["user"] = operated_user
        if user.is_superuser:
            return attrs
        else:
            project_user = ProjectUser.objects.get(user=user, project=project)
            if project_user.role == "project_owner" and role == "user":
                return attrs
            else:
                raise PermissionDenied("权限不足")


class UpdateProjectRoleSerializer(serializers.ModelSerializer):
    user = SubUserSerializer(read_only=True)
    project = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ProjectUser
        fields = ("user", "role", "project")

    def validate(self, attrs):
        user = self.context["request"].user
        user = User.objects.get(pk=user.id)
        project_id = self.context["view"].kwargs["project_id"]
        project = get_object_or_404(Project, pk=project_id)
        operated_user_id = self.context["view"].kwargs["pk"] or attrs["user_id"]
        operated_user = get_object_or_404(User, pk=operated_user_id)
        attrs["project"] = project
        attrs["user"] = operated_user
        if user.is_superuser:
            return attrs
        else:
            raise PermissionDenied("权限不足")


class AddDocumentOperatingHistorySerializer(serializers.Serializer):
    doc_id = serializers.IntegerField(label="文本id", min_value=1)
    operation = serializers.CharField()
    datetime = serializers.DateTimeField(read_only=True)
    title = serializers.CharField(read_only=True)
    project_name = serializers.CharField(read_only=True)
    project_url = serializers.CharField(read_only=True)
    doc_url = serializers.CharField(read_only=True)
    def validate_doc_id(self, value):
        """
        检验doc是否存在
        """
        try:
            doc = Document.objects.get(id=value)
        except Document.DoesNotExist:
            raise serializers.ValidationError('该文本不存在')
        return value


    def create(self, validated_data):
        #TODO
        doc_id = validated_data['doc_id']
        doc = Document.objects.get(id=doc_id)
        validated_data["text"] = doc.text
        datetime_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        validated_data["datetime"] = datetime_str
        dict = {}
        dict["doc_id"] = validated_data["doc_id"]
        dict["operation"] = validated_data["operation"]
        dict["datetime"] = datetime_str
        cart_pickle = pickle.dumps(dict)
        str = base64.b64encode(cart_pickle).decode()
        user = self.context['request'].user
        redis_conn = get_redis_connection('history')
        pl = redis_conn.pipeline()
        redis_hash_key = 'history_%s' % user.id
        redis_list_key = 'history_list_%s' % user.id
        pl.hset(redis_hash_key, doc_id, str)
        if redis_conn.llen(doc_id) > constants.USER_OPERATE_HISTORY_MAX_LIMIT:
            pl.hdel(pl.lindex(redis_list_key,-1))
        pl.lrem(redis_list_key, 0, doc_id)
        pl.lpush(redis_list_key, doc_id)
        pl.ltrim(redis_list_key, 0, constants.USER_OPERATE_HISTORY_MAX_LIMIT - 1)
        pl.execute()
        return validated_data

class TrainLabelSerializer(serializers.ModelSerializer):
    text = serializers.CharField(read_only=True)
    class Meta:
        model = Label
        fields = ["text"]
class subAnnotationSerializer(serializers.ModelSerializer):

    label = TrainLabelSerializer(read_only=True)

    class Meta:
        model = Annotation
        fields = ["label","start_offset", "end_offset",]

class DocumentFromDBSerializer(serializers.ModelSerializer):
    text = serializers.CharField(read_only=True)
    annotations = subAnnotationSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = ('id', "text",  "annotations")

class MyCharField(serializers.CharField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        validator = EmailValidator(message=self.error_messages['invalid'])
        self.validators.append(validator)

class AssignTaskSerializer(serializers.Serializer):
    doc_status = serializers.MyCharField()
