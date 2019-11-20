from itsdangerous import TimedJSONWebSignatureSerializer,BadData

from api.models import User
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


