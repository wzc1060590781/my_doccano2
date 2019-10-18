from pymysql import DatabaseError
from rest_framework import status
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    # 先调用REST framework默认的异常处理方法获得标准错误响应对象
    response = exception_handler(exc, context)

    # 在此处补充自定义的异常处理
    if response is not None:
        response.data['status'] = response.status_code
        if response.status_code == 404:
            response.data['message'] = "不存在该资源"
            response.data['success'] = False
        del response.data["detail"]
        response.data["data"] = []

    if response is None:
        # view = context['view']
        if isinstance(exc, DatabaseError):
            # 数据库异常
            # logger.error('[%s] %s' % (view, exc))
            response.data['status'] = status.HTTP_507_INSUFFICIENT_STORAGE
            response.data['message'] = "服务器内部错误"
            response.status = status.HTTP_507_INSUFFICIENT_STORAGE
        # response.data["message"] = "异常"
    return response
