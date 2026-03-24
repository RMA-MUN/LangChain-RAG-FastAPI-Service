from rest_framework.response import Response
from rest_framework.views import APIView
from shortuuid import uuid
from apps.file.serializers import ImgSerializer
from django.conf import settings
from apps.user.authentications import JWTAuthentication
from apps.user.models import User
from apps.utils.cache_utils import clear_user_cache

import os

class UploadAPIView(APIView):
    """文件上传"""
    authentication_classes = [JWTAuthentication]

    def post(self, request, *args, **kwargs) -> Response:
        """文件上传"""
        # 验证用户是否已登录
        if not request.user or not request.user.is_authenticated:
            return Response(
                {
                    "errno": 1,
                    "message": "请先登录"
                },
                status=401
            )
        
        serializer = ImgSerializer(data=request.data)
        if serializer.is_valid():
            img = serializer.validated_data['img']
            # 生成一个随机字符串充当文件名，并使用实际文件的扩展名
            filename = uuid() + os.path.splitext(img.name)[1]
            # 保存文件到media/img目录
            filepath = settings.MEDIA_ROOT / 'img' / filename
            try:
                with open(filepath, 'wb') as f:
                    for chunk in img.chunks():
                        f.write(chunk)
            except Exception as e:
                print(e)
                return Response(
                 {
                     "errno": 1,
                     "message": "图片上传失败"
                }
                )
            # 返回文件的URL
            # 示例：http://localhost:8000/media/img/202308251423523423423.png
            file_url = settings.MEDIA_URL + 'img/' + filename
            
            # 更新用户的avatar字段
            try:
                user = request.user
                user.avatar = file_url
                user.save()
                # 清除用户缓存
                clear_user_cache(user.uuid)
            except Exception as e:
                print(e)
                # 即使更新用户信息失败，也要返回文件上传成功的响应
                pass
            
            # 返回文件的URL
            return Response(
                {
                    "success": True,
                    "data": {
                        "url": file_url,
                        "alt": "当前加载较为缓慢，请稍后重试",
                        "href": file_url
                    }
                }
            )
        else:
            from rest_framework import status
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)