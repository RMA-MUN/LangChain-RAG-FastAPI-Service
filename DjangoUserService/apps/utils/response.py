from rest_framework.response import Response

def success_response(data=None, message="操作成功", status=200):
    """
    成功响应
    :param data: 响应数据
    :param message: 响应消息
    :param status: HTTP状态码
    :return: Response对象
    """
    return Response({
        "code": status,
        "message": message,
        "data": data
    }, status=status)

def error_response(message="操作失败", status=400, code=None):
    """
    错误响应
    :param message: 错误消息
    :param status: HTTP状态码
    :param code: 自定义错误码
    :return: Response对象
    """
    return Response({
        "code": code or status,
        "message": message,
        "data": None
    }, status=status)
