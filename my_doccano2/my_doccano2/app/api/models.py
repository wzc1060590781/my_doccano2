import string

from django.contrib.auth.models import AbstractUser, Group, UserManager
from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer,BadData

from api import constants
from app import settings

DOCUMENT_CLASSIFICATION = 'DocumentClassification'
SEQUENCE_LABELING = 'SequenceLabeling'
SEQ2SEQ = 'Seq2seq'
PROJECT_CHOICES = (
    (DOCUMENT_CLASSIFICATION, 'document classification'),
    (SEQUENCE_LABELING, 'sequence labeling'),
    (SEQ2SEQ, 'sequence to sequence'),
)


class BaseModel(models.Model):
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间", help_text="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间", help_text="更新时间")

    class Meta:
        abstract = True


class User(AbstractUser):
    phone_number = models.CharField(max_length=11, null=True, verbose_name="手机号")
    is_delete = models.BooleanField(default=False)

    def __str__(self):
        return self.username

    def delete(self, using=None, keep_parents=False):
        self.is_delete = True
        self.save()

    class Meta:
        db_table = "tb_users"
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    @staticmethod
    def check_verify_email_token(token):
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=constants.VERIFY_EMAIL_TOKEN_EXPIRES)
        try:
            data = serializer.loads(token)
        except BadData:
            return None
        else:
            user_id = data['user_id']
            email = data['email']
            try:
                user = User.objects.get(id=user_id, email=email)
            except User.DoesNotExist:
                return None
            else:
                return user




class Project(BaseModel):
    name = models.CharField(max_length=20, unique=True, verbose_name="项目名称", help_text="项目名称")
    randomize_document_order = models.BooleanField(default=False, verbose_name="是否乱序", help_text="是否乱序")
    description = models.TextField(default='', help_text="项目描述信息")
    project_type = models.CharField(max_length=30, choices=PROJECT_CHOICES, help_text="项目类型")
    pic = models.ImageField(upload_to='project/',default="project/default.jpg")
    users = models.ManyToManyField(
        User,
        through='ProjectUser',  ## 自定义中间表
        through_fields=('project', 'user'), help_text="用户"
    )

    class Meta:
        db_table = "projects"
        verbose_name = "项目表"

    def __str__(self):
        return self.name


Roles = (
    ('project_owner', 'project_owner'),
    ('user', 'user')
)


class ProjectUser(BaseModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE,
                                help_text="项目")
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="用户")
    # TODO
    role = models.CharField(max_length=20, blank=True, null=False, choices=Roles, default="user")

    class Meta:
        db_table = "project_user_relationship"
        verbose_name = "项目用户表"
        unique_together = (
            ('project', 'user'),
        )


class Document(BaseModel):
    project = models.ForeignKey("Project", related_name="documents", blank=True, on_delete=models.SET_NULL, null=True,
                                verbose_name="所属项目", help_text="所属项目")
    text = models.TextField(verbose_name="文书内容", help_text="文书内容")
    is_annoteated = models.BooleanField(default=False, verbose_name="文本是否已被标注", help_text="是否被标注")
    is_delete = models.BooleanField(default=False, verbose_name="文本是否被逻辑删除", help_text="是否被删除")
    title = models.CharField(verbose_name="文档标题", max_length=100, null=True, help_text="文档标题")

    class Meta:
        db_table = "documents"
        verbose_name = "文书表"

    def __str__(self):
        return self.text[:50]

    def delete(self, using=None, keep_parents=False):
        """重写数据库删除方法实现逻辑删除"""
        self.is_delete = True
        self.save()


class Annotation(BaseModel):
    document = models.ForeignKey(Document, related_name="annotations", on_delete=models.CASCADE,
                                 verbose_name="所属文本")
    # 概率
    prob = models.FloatField(default=0.0)
    # 是否人工标注
    annoted_by = models.ForeignKey("User", related_name="annotations", null=True, on_delete=models.SET_NULL,
                                   verbose_name="打标签者")
    manual = models.BooleanField(default=False)
    # 所用标记
    label = models.ForeignKey("Label", related_name="annotations", on_delete=models.CASCADE, null=True,
                              verbose_name="标记")
    # 文档中的开始位置
    start_offset = models.IntegerField(verbose_name="标记开始下标")
    # 文档中的结束位置
    end_offset = models.IntegerField(verbose_name="标记结束下标")

    class Meta:
        db_table = "annotations"
        verbose_name = "标签表"
        unique_together = (
            ('start_offset', 'end_offset', "document"),
        )


class Label(BaseModel):
    PREFIX_KEYS = (
        ('ctrl', 'ctrl'),
        ('shift', 'shift'),
        ('ctrl shift', 'ctrl shift')
    )
    SUFFIX_KEYS = tuple(
        (c, c) for c in string.ascii_lowercase
    )
    text = models.CharField(max_length=100)
    background_color = models.CharField(max_length=7, default='#209cee')
    project = models.ForeignKey(Project, related_name='labels', on_delete=models.CASCADE)
    prefix_key = models.CharField(max_length=10, blank=True, null=True, choices=PREFIX_KEYS)
    suffix_key = models.CharField(max_length=10, blank=True, null=True, choices=SUFFIX_KEYS)

    class Meta:
        db_table = "labels"
        verbose_name = "标记表"
        unique_together = (
            ('project', 'text'),
            ('project','prefix_key', 'suffix_key'),
        )

    def __str__(self):
        return self.text


class Algorithm(BaseModel):
    algorithm_type = models.CharField(max_length=30, choices=PROJECT_CHOICES, help_text="算法类型")
    name = models.CharField(max_length=100, unique=True)
    mini_quantity = models.IntegerField(null=False, verbose_name="最小训练集")
    code_url = models.CharField(max_length=255, null=True,verbose_name="算法代码路径")
    model_url = models.CharField(max_length=255, null=True, verbose_name="算法模型路径")
    description = models.TextField(default="", verbose_name="算法描述")
    is_delete = models.BooleanField(default=False, verbose_name="算法是否删除删除")

    def __str__(self):
        return self.name

    def delete(self, using=None, keep_parents=False):
        self.is_delete = True
        self.save()

