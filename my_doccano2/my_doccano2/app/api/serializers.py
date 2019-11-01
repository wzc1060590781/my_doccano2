import json
import re

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import Group
from django.db import transaction, DatabaseError
from django.db.models import Q
from django.http import Http404
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

from .models import User, Project, ProjectUser, Document, Label, Annotation


class CreateUserSerializer(serializers.ModelSerializer):
    """创建用户的序列化器"""
    password2 = serializers.CharField(label='确认密码', write_only=True)
    phone_number = serializers.CharField(label="手机号")

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password2', "phone_number", "system_role")
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
        exsist_user = User.objects.filter(phone_number=phone_number, username=username)
        if not exsist_user:
            if User.objects.filter(phone_number=phone_number):
                raise serializers.ValidationError('手机号已存在')
        user = self.context["request"].user
        if data["system_role"] == "super_user":
            raise PermissionDenied("无法创建或修改超级管理员用户")
        if data["system_role"] == "system_manager" and not user.is_superuser:
            raise PermissionDenied("权限不足")
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
        return user


class UpdateOtherUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', "phone_number", "system_role")

    def validate(self, data):
        user = self.context["request"].user
        operated_user_id = self.context["view"].kwargs["pk"]
        if operated_user_id:
            if User.objects.get(pk=operated_user_id).system_role == "super_user":
                raise PermissionDenied("无法创建或修改超级管理员用户")
            elif User.objects.get(pk=operated_user_id).system_role == "system_manager":
                if not user.is_superuser:
                    raise PermissionDenied("权限不足")

        if data["system_role"] == "super_user":
            raise PermissionDenied("无法创建或修改超级管理员用户")
        if data["system_role"] == "system_manager" and not user.is_superuser:
            raise PermissionDenied("权限不足")
        return data


class UpdateSelfSerializer(serializers.ModelSerializer):
    system_role = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', "phone_number", "system_role")
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


class ChangePasswordSerializer(serializers.ModelSerializer):
    username = serializers.CharField(read_only=True)
    new_password = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)
    system_role = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'new_password', "new_password2", "phone_number", "system_role")
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
        if not check_password(self.context["request"].get("password"), user.password):
            raise serializers.ValidationError("密码错误")
        # 判断两次密码
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError('两次密码不一致')

    def create(self, validated_data):
        del validated_data["password"]
        del validated_data["new_password2"]
        # password = validated_data["password"]
        user = super().create(validated_data)
        user.set_password(validated_data["new_password"])
        user.save()
        return user


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ["id", "text", "background_color", "text_color", "project_id", "prefix_key", "suffix_key"]

        extra_kwargs = {
            'background_color': {
                'min_length': 7,
                'max_length': 7,
                'error_messages': {
                    'min_length': '颜色长度必须为7',
                    'max_length': '颜色长度必须为7',
                }
            },
            'text_color': {
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
        text_color = attrs["text_color"]
        if background_color == text_color:
            raise serializers.ValidationError("文字颜色和背景颜色不能一样")
        project_id = self.context["view"].kwargs["project_id"]
        labels_queryset = Label.objects.filter(project_id=project_id)
        if labels_queryset.filter(Q(text=text) | Q(background_color=background_color)).count() != 0:
            raise serializers.ValidationError("项目中已存在该标签或已存在该颜色标签")
        project = Project.objects.get(pk=int(project_id))
        attrs["project"] = project
        return attrs


class SubLabelSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    text = serializers.CharField(read_only=True)

    class Meta:
        model = Label
        fields = ["id", "text"]


class AnnotationSerializer(serializers.ModelSerializer):
    prob = serializers.DecimalField(max_digits=4, decimal_places=3, max_value=1.0, min_value=0.0, read_only=True)
    manual = serializers.BooleanField(read_only=True)
    label = SubLabelSerializer()
    annoted_by = serializers.CharField(read_only=True)
    document = serializers.CharField(read_only=True)

    class Meta:
        model = Annotation
        fields = ["id", "document", "prob", "manual", "label", "start_offset", "end_offset", "annoted_by"]

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
        attrs["document"] = document
        return attrs

    def create(self, validated_data):
        document_id = validated_data["document"].id
        document = get_object_or_404(Document, pk=document_id)
        with transaction.atomic():
            save_id = transaction.savepoint()
            # if not document.is_annoteated:
            #     document.is_annoteated = True
            #     document.save()
            while True:
                label_id = validated_data["label"]["id"]
                label = get_object_or_404(Label, pk=label_id)
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
                        transaction.rollback(save_id)
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
                        transaction.rollback(save_id)
                        continue

            #         try:
            #             annotation = Annotation.objects.create(start_offset=start_offset, end_offset=end_offset,
            #                                                    document_id=document.id,
            #                                                    annoted_by=annoted_by, manual=True)
            #             return annotation
            #         except Exception:
            #             annotation = Annotation.objects.filter(start_offset=start_offset, end_offset=end_offset,
            #                                                    document_id=document.id)
            #             if annotation:
            #                 result = Annotation.objects.filter(start_offset=start_offset, end_offset=end_offset,
            #                                                    document_id=document.id,
            #                                                    annoted_by=annotation.annoted_by).update(
            #                     label=label,
            #                     annoted_by=annoted_by,
            #                     manual=True)
            #                 if result:
            #                     return Annotation(start_offset=start_offset, end_offset=end_offset,
            #                                       document_id=document.id, annoted_by=annoted_by, label=label,
            #                                       manual=True)
            #                 else:
            #                     transaction.rollback(save_id)
            #             else:
            #                 continue
            # except:
            #     transaction.rollback(save_id)


class DocumentSerializer(serializers.ModelSerializer):
    text_upload = serializers.FileField(write_only=True)
    text = serializers.CharField(read_only=True)
    annotations = AnnotationSerializer(many=True, read_only=True)
    is_annoteated = serializers.BooleanField(default=False)
    title = serializers.CharField(read_only=True)

    class Meta:
        model = Document
        fields = ('id', "text_upload", "text", 'project', "is_annoteated", "annotations", "title")

    def validate(self, attrs):
        text = attrs.get("text_upload", None)
        text_str = text.read().decode("utf-8")
        if not text:
            raise serializers.ValidationError('未上传文件')
        if not (text.name.endswith(".txt") or text.name.endswith(".json")):
            raise serializers.ValidationError('文件格式有误，请上传.txt格式文件，或json格式文件')
        if text.name.endswith(".json"):
            try:
                text_dict = json.loads(text_str)
            except:
                raise serializers.ValidationError("文本格式有误")
            # TODO
            text_str = text_dict.get("文书内容", None)
        if Document.objects.filter(text=text_str).count():
            raise serializers.ValidationError('文件已存在，请勿重复上传')
        attrs["text"] = text_str
        try:
            title = re.match(r"(.*?)\.(.*?)", text.name).group(1)
        except:
            raise serializers.ValidationError("文件名有误")
        attrs["title"] = title
        return attrs

    def create(self, validated_data):
        del validated_data["text_upload"]
        project_id = self.context["view"].kwargs["project_id"]
        project = Project.objects.get(pk=int(project_id))
        validated_data["project"] = project
        return super().create(validated_data)


class ProjectSerializer(serializers.ModelSerializer):
    count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'name', "description", "project_type", "randomize_document_order", "count")


class SubProjectSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)

    class Meta:
        model = Project
        fields = ["id", "name", "description"]


class SubUserSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    username = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "phone_number"]


class ProjectUserSerializer(serializers.ModelSerializer):
    project = SubProjectSerializer()
    user = SubUserSerializer()

    class Meta:
        model = ProjectUser
        fields = ('id', 'user', "project", "role")

    def validate(self, attrs):
        project_id = attrs["project"]["id"]
        role = attrs["role"]
        user = self.context["request"].user
        if user.is_superuser or user.system_role == "system_manager":
            return attrs
        user_id = self.context["request"].user.id
        project_user = ProjectUser.objects.get(project_id=project_id, user_id=user_id)
        if project_user:
            if project_user.role == "project_owner" and role == "ordinary_user":
                return attrs
            raise serializers.ValidationError("无操作权限")
        else:
            raise serializers.ValidationError("无操作权限")

    def create(self, validated_data):
        project_id = validated_data["project"]["id"]
        project = get_object_or_404(Project, pk=project_id)
        operated_user_id = validated_data["user"]["id"]
        operated_user = get_object_or_404(User, pk=operated_user_id)
        role = validated_data["role"]
        project_user = ProjectUser.objects.create(project=project, user=operated_user, role=role)
        project_user.save()
        return project_user
