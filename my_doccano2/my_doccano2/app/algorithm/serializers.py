import os

from django.shortcuts import get_object_or_404
from rest_framework import serializers

from algorithm.models import Algorithm
from app import settings


class AlgorithmSerializer(serializers.ModelSerializer):
    model_url = serializers.CharField(read_only=True)
    class Meta:
        model = Algorithm
        fields = (
            "id", "algorithm_type", "name", "mini_quantity", "model_url", "description", "algorithm_file")
    def validate(self, attrs):
        f = self.context["request"].FILES.get('algorithm_file', None)
        if self.context["view"].action == "create":
            if not f:
                raise serializers.ValidationError('未上传文件')
            if not f.name.endswith(".exe"):
                raise serializers.ValidationError('文件格式有误，请上传.py格式文件')
            path = os.path.join(settings.ALGORITHM_ROOT,f.name)
            if os.path.exists(path):
                raise serializers.ValidationError("该文件名已存在，请勿重复上传")
        elif self.context["view"].action == "update":
            if f:
                if not f.name.endswith(".exe"):
                    raise serializers.ValidationError('文件格式有误，请上传.py格式文件')
                algorithm_id = self.context["view"].kwargs["pk"]
                algorithm = get_object_or_404(Algorithm,pk=algorithm_id)
                os.remove(algorithm.algorithm_file.path)
                path = os.path.join(settings.ALGORITHM_ROOT, f.name)
                if os.path.exists(path):
                    raise serializers.ValidationError("该文件名已存在，请勿重复上传")
        return attrs
    def create(self, validated_data):
        return super().create(validated_data)

class UpdateAlgorithmSerializer(serializers.ModelSerializer):
    model_url = serializers.CharField(read_only=True)
    class Meta:
        model = Algorithm
        fields = (
            "id", "algorithm_type", "name", "mini_quantity","model_url", "description", "algorithm_file")

    def validate(self, attrs):
        f = self.context["request"].FILES.get('algorithm_file', None)
        if not f:
            return attrs
        if not f.name.endswith(".py"):
            raise serializers.ValidationError('文件格式有误，请上传.py格式文件')
        return attrs