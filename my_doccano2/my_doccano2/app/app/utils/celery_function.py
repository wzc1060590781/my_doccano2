from itsdangerous import TimedJSONWebSignatureSerializer,BadData
from pymysql import DatabaseError

from api.models import User
from app import settings
from app.utils import constants


def generate_verify_email_url(user_id,email):
    """
    生成验证邮箱的url
    """
    serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=constants.VERIFY_EMAIL_TOKEN_EXPIRES)
    data = {'user_id': user_id, 'email': email}
    token = serializer.dumps(data).decode()
    verify_url = 'http://121.41.4.174/find_password.html?token=' + token
    return verify_url


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