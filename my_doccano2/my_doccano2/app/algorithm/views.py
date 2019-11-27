from django.shortcuts import render

# Create your views here.
from rest_framework.viewsets import ModelViewSet

from algorithm import serializers
from algorithm.models import Algorithm


class AlgorithmView(ModelViewSet):
    serializer_class = serializers.AlgorithmSerializer
    queryset = Algorithm.objects.all()
