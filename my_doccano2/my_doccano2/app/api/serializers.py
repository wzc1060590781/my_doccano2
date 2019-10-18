import json
import re

from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers

from .models import User, Project, Project_User, Document, Label, Annotation


class CreateUserSerializer(serializers.ModelSerializer):
    """创建用户的序列化器"""
    password2 = serializers.CharField(label='确认密码', write_only=True)
    project_id = serializers.CharField(label="所在项目", write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password2', "project_id")
        extra_kwargs = {
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }

    def validate_project_id(self, project_id):
        print(project_id)
        try:
            id = int(project_id)
        except Exception:
            raise serializers.ValidationError("项目id必须为整数")
        try:
            project = Project.objects.get(pk=id)
        except Exception:
            raise serializers.ValidationError('该项目不存在')

    def validate(self, data):
        # 判断两次密码
        if data['password'] != data['password2']:
            raise serializers.ValidationError('两次密码不一致')
        return data

    def create(self, validated_data):
        """重写保存方法，增加密码加密"""

        # 移除数据库模型类中不存在的属性
        del validated_data['password2']
        user = super().create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        Project_User.save(project_id=validated_data["project_id"], user_id=user.id)
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
            print(i)
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
    class Meta:
        model = Label
        fields = ["text"]


class AnnotationSerializer(serializers.ModelSerializer):
    prob = serializers.DecimalField(max_digits=4, decimal_places=3, max_value=1.0, min_value=0.0)
    manual = serializers.BooleanField(write_only=True)
    label = SubLabelSerializer(read_only=True)

    class Meta:
        model = Annotation
        fields = ["id", "document_id", "prob", "user", "manual", "label", "start_offset", "end_offset"]

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
        print(document_id)
        document = Document.objects.get(pk=int(document_id))
        if end_offset > len(document.text):
            raise serializers.ValidationError("结束下标不得超出文本长度")
        attrs["document"] = document
        return attrs

    def create(self, validated_data):
        document = validated_data["document"]
        if not document.is_annoteated:
            document.is_annoteated = True
            document.save()
        return super().create(validated_data)


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
    # documents = DocumentSerializer(many=True, read_only=True)
    count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = ('id', "owner", 'name', "description", "project_type", "randomize_document_order", "count")
