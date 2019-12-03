from itsdangerous import TimedJSONWebSignatureSerializer,BadData

from api.models import User, Document
from api.serializers import DocumentFromDBSerializer
from app import settings
from api import constants


def generate_verify_email_url(user_id,email):
    """
    生成验证邮箱的url
    """
    serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=constants.VERIFY_EMAIL_TOKEN_EXPIRES)
    data = {'user_id': user_id, 'email': email}
    token = serializer.dumps(data).decode()
    verify_url = 'http://127.0.0.1/find_password.html?token=' + token
    return verify_url


def generate_doc_list(project_id):
    docs = Document.objects.filter(project_id=project_id, is_annoteated=True)
    serializers = DocumentFromDBSerializer(docs, many=True)
    doc_list = []
    for serializer_dict in serializers.data:
        dict = {}
        dict["id"] = serializer_dict["id"]
        dict["text"] = serializer_dict["text"]
        annotation_list = []
        for annotation in serializer_dict["annotations"]:
            label_dict = {}
            label_dict["text"] = annotation["label"]["text"]
            label_dict["start_offset"] = annotation["start_offset"]
            label_dict["end_offset"] = annotation["end_offset"]
            annotation_list.append(label_dict)
        dict["label"] = annotation_list
        doc_list.append(dict)
    return doc_list