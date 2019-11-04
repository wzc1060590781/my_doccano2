def jwt_response_payload_handler(token, user=None, request=None):
    """
    自定义jwt认证成功返回数据
    """
    return {
        "status": 200,
        "success": True,
        "message": "成功",
        "data": {
            "user_id": user.id,
            "username": user.username,
            "token": token
        }
    }
