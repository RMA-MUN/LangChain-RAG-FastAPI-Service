import logging

from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    # 先调用DRF默认的异常处理器
    response = exception_handler(exc, context)

    # 1. 处理DRF能识别的异常（认证、参数校验、权限等）
    if response is not None:
        # 统一返回标准化格式，绝对不返回堆栈
        return Response(
            data={
                "code": response.status_code,
                "msg": response.data.get("detail", "请求参数错误，请检查"),
                "data": None
            },
            status=status.HTTP_200_OK  # 业务错误用code区分，HTTP状态码统一200也可，按需调整
        )

    # 2. 处理DRF无法识别的系统异常（代码报错、数据库异常等）
    logger.error(f"系统未捕获异常", exc_info=exc)  # 堆栈信息只记录到服务端日志
    return Response(
        data={
            "code": 500,
            "msg": "系统繁忙，请稍后再试",  # 对外只返回友好提示，绝对不返回堆栈
            "data": None
        },
        status=status.HTTP_200_OK
    )