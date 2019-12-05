import os

from django.core.files.storage import FileSystemStorage
from django.db import models
from api.models import BaseModel, Project
from app import settings

DOCUMENT_CLASSIFICATION = 'DocumentClassification'
SEQUENCE_LABELING = 'SequenceLabeling'
SEQ2SEQ = 'Seq2seq'

PROJECT_CHOICES = (
    (DOCUMENT_CLASSIFICATION, 'document classification'),
    (SEQUENCE_LABELING, 'sequence labeling'),
    (SEQ2SEQ, 'sequence to sequence'),
)

class Algorithm(BaseModel):
    algorithm_type = models.CharField(max_length=30, choices=PROJECT_CHOICES, help_text="算法类型")
    name = models.CharField(max_length=100, unique=True)
    mini_quantity = models.IntegerField(null=False, verbose_name="最小训练集")
    algorithm_file = models.FileField(upload_to='algorithm/')
    # algorithm_path = models.CharField(max_length=200, default="")
    model_url = models.CharField(max_length=255, null=True, verbose_name="算法模型路径")
    description = models.TextField(default="", verbose_name="算法描述")
    is_delete = models.BooleanField(default=False, verbose_name="算法是否删除删除")
    project = models.ManyToManyField(
        Project,
        through='AlgorithmProject',  ## 自定义中间表
        through_fields=('algorithm', 'project'), help_text="项目"
    )

    def __str__(self):
        return self.name

    def delete(self, using=None, keep_parents=False):
        self.is_delete = True
        self.save()


class AlgorithmProject(BaseModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE,
                                help_text="项目")
    algorithm = models.ForeignKey(Algorithm, on_delete=models.CASCADE, help_text="用户")
    # TODO
    model_url = models.CharField(max_length=200,null=True)
    config = models.FileField(upload_to="configs/")

    class Meta:
        db_table = "algorithm_project_tb"
        verbose_name = "算法项目表"
        unique_together = (
            ('project', 'algorithm'),
        )
