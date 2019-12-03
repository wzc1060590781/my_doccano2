from django.shortcuts import render, get_object_or_404

# Create your views here.
from rest_framework import mixins

from rest_framework.viewsets import ModelViewSet

from algorithm import serializers
from algorithm.models import Algorithm
from api.models import Project
from app.utils.Viewset import ApiModelViewSet


class AlgorithmView(ApiModelViewSet):
    serializer_class = serializers.AlgorithmSerializer
    queryset = Algorithm.objects.all()

    def update(self, request, *args, **kwargs):
        partial = True
        return super().update(request, *args, **kwargs)

