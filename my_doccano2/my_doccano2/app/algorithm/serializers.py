import os

from rest_framework import serializers

from algorithm.models import Algorithm


# class AlgorithmSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Algorithm
#         fields = ["id","algorithm_type","name","mini_quantity","code_url","model_url","description"]
from app import settings


class AlgorithmSerializer(serializers.ModelSerializer):
    model_url = serializers.CharField(read_only=True)
    # algorithm_file =serializers.FileField()
    class Meta:
        model = Algorithm
        fields = (
            "id", "algorithm_type", "name", "mini_quantity", "model_url", "description", "algorithm_file")

    def validate(self, attrs):
        f = self.context["request"].FILES.get('algorithm_file', None)
        if not f:
            raise serializers.ValidationError('未上传文件')
        if not f.name.endswith(".py"):
            raise serializers.ValidationError('文件格式有误，请上传.py格式文件')

        return attrs
    def create(self, validated_data):
        # del validated_data["algorithm_file"]
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