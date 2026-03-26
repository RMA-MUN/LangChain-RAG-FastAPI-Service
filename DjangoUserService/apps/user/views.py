"""
视图模块：
    - LoginView(post): 类视图，用于用户登录，验证用户登录信息，并调用jwt生成器生成token

    - ResetPasswordView(post): 类视图，继承自AuthenticatedView父类用于身份验证，重置用户密码

    - TokenRefreshView(post): 类视图，返回刷新后的token

    - UserDetailView(get): 类视图，返回序列化后的当前用户信息

"""
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.views import APIView

from .serializers import LoginSerializer, UserSerializer, ResetPasswordSerializer, RegisterSerializer, UserUpdateSerializer
from datetime import datetime
from .authentications import JWTAuthentication, JWTTokenGenerator
from rest_framework.response import Response
from rest_framework import status
from .fatherClass import AuthenticatedView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..utils.cache_utils import cache_user_info, clear_user_cache
from ..utils.rate_limit_utils import rate_limit

# Create your views here.

authentication = JWTAuthentication()
jwttoken = JWTTokenGenerator()


class LoginView(APIView):
    """类视图，处理用户登录"""
    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="登录成功",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "user": UserSerializer,
                        "token": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(description="登录失败")
        }
    )
    def post(self, request) -> Response:
        """
        处理post请求，验证用户登录
        :param request: post请求，包含用户登录信息
        :return: Response对象，包含登录成功信息，用户对象和token
        """
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data.get('user')  # 从序列化器中获取用户对象
            user.last_login = datetime.now()  # 更新用户最后登录时间
            user.save()  # 保存用户对象
            # 生成JWT token - 正确处理返回的元组
            token, expire_time = jwttoken.generate_token(user)
            return Response({"message": f"{user.username} 登录成功", "user": UserSerializer(user).data, "token": token}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    """类视图，处理用户注册"""
    @swagger_auto_schema(
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response(
                description="注册成功",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "status": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "user": UserSerializer,
                        "token": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(description="注册失败")
        }
    )
    # @rate_limit(limit=1, window=60)
    def post(self, request) -> Response:
        """
        处理post请求，用户注册
        :param request: post请求，包含用户注册信息
        :return: Response对象，包含注册成功信息，用户对象和token
        """
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()  # 调用序列化器的create方法创建用户
            # 生成JWT token
            token, expire_time = jwttoken.generate_token(user)
            return Response({"status": 201, "message": f"{user.username} 注册成功", "user": UserSerializer(user).data, "token": token}, status=status.HTTP_201_CREATED)
        else:
            return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(AuthenticatedView):
    """类视图，处理用户重置密码"""
    @swagger_auto_schema(
        request_body=ResetPasswordSerializer,
        responses={
            200: openapi.Response(
                description="密码重置成功",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "token": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(description="密码重置失败")
        }
    )
    def post(self, request) -> Response:
        """
        处理post请求，重置用户密码
        :param request: old_password, new_password, confirm_password
        :return: Response对象，包含重置密码成功或失败的信息
        """

        serializer = ResetPasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # 获取旧token并添加到黑名单
            auth_header = request.headers.get('Authorization')
            if auth_header:
                try:
                    auth_type, token = auth_header.split(' ', 1)
                    if auth_type.lower() == 'bearer':
                        jwttoken.blacklist_token(token)
                except ValueError:
                    pass
            
            user = serializer.validated_data.get('user')  # 从序列化器中获取用户对象
            user.set_password(serializer.validated_data.get('new_password'))  # 设置新密码
            user.save()  # 保存用户对象
            # 清除用户缓存
            clear_user_cache(user.uuid)
            # 生成新token
            new_token, expire_time = jwttoken.generate_token(user)
            return Response({
                "message": "密码重置成功",
                "token": new_token
            }, status=status.HTTP_200_OK)
        else:
            return Response({"detail": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class TokenRefreshView(APIView):
    """处理Token刷新请求"""
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['token'],
            properties={
                'token': openapi.Schema(type=openapi.TYPE_STRING, description="旧Token")
            }
        ),
        responses={
            200: openapi.Response(
                description="Token刷新成功",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "token": openapi.Schema(type=openapi.TYPE_STRING),
                        "expire_time": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(description="Token刷新失败"),
            401: openapi.Response(description="Token无效")
        }
    )
    def post(self, request) -> Response:
        """
        处理post请求，刷新用户Token
        :param request: post请求，包含旧Token
        :return: Response对象，包含新Token和过期时间
        """
        token = request.data.get('token')
        if not token:
            return Response({
                "detail": "Token不能为空"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            new_token, expire_time = jwttoken.refresh_token(token)
            # 将旧token添加到黑名单
            jwttoken.blacklist_token(token)
            return Response({
                "message": "Token刷新成功",
                "token": new_token,
                "expire_time": expire_time
            }, status=status.HTTP_200_OK)
        except AuthenticationFailed as e:
            return Response({
                "detail": str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({
                "detail": "Token刷新失败"
            }, status=status.HTTP_400_BAD_REQUEST)

@cache_user_info()
def get_user_info(user):
    serializer = UserSerializer(user)
    return {
        "id": serializer.data.get('uuid'),
        "username": serializer.data.get('username'),
        "email": serializer.data.get('email'),
        "avatar": serializer.data.get('avatar'),
        "telephone": serializer.data.get('telephone'),
        "gender": serializer.data.get('gender'),
        "bio": serializer.data.get('bio'),
        "create_time": serializer.data.get('date_joined'),
        "last_login": serializer.data.get('last_login'),
    }

class UserDetailView(AuthenticatedView):
    """获取当前登录用户详情"""
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="获取用户详情成功",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_STRING),
                                "username": openapi.Schema(type=openapi.TYPE_STRING),
                                "email": openapi.Schema(type=openapi.TYPE_STRING),
                                "avatar": openapi.Schema(type=openapi.TYPE_STRING),
                                "telephone": openapi.Schema(type=openapi.TYPE_STRING),
                                "gender": openapi.Schema(type=openapi.TYPE_STRING),
                                "bio": openapi.Schema(type=openapi.TYPE_STRING),
                                "create_time": openapi.Schema(type=openapi.TYPE_STRING),
                                "last_login": openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    }
                )
            )
        }
    )
    def get(self, request) -> Response:
        """
        处理get请求，获取当前登录用户详情
        :param request: get请求
        :return: Response对象，包含用户详情
        """
        user_info = get_user_info(request.user)
        return Response({
            "success": True,
            "message": "获取用户详情成功",
            "data": user_info
        }, status=status.HTTP_200_OK)


class UserUpdateView(AuthenticatedView):
    """更新当前登录用户信息"""
    @swagger_auto_schema(
        request_body=UserUpdateSerializer,
        responses={
            200: openapi.Response(
                description="用户信息更新成功",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "user": UserSerializer,
                        "token": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(description="用户信息更新失败")
        }
    )
    def put(self, request) -> Response:
        """
        处理put请求，更新当前登录用户信息
        :param request: put请求，包含用户更新信息
        :return: Response对象，包含更新成功信息和更新后的用户对象
        """
        serializer = UserUpdateSerializer(data=request.data, instance=request.user, context={'request': request})
        if serializer.is_valid():
            # 获取旧token并添加到黑名单
            auth_header = request.headers.get('Authorization')
            if auth_header:
                try:
                    auth_type, token = auth_header.split(' ', 1)
                    if auth_type.lower() == 'bearer':
                        jwttoken.blacklist_token(token)
                except ValueError:
                    pass
            
            user = serializer.save()  # 调用序列化器的update方法更新用户
            # 清除用户缓存
            clear_user_cache(user.uuid)
            # 生成新token
            new_token, expire_time = jwttoken.generate_token(user)
            return Response({"message": "用户信息更新成功", "user": UserSerializer(user).data, "token": new_token}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UserLogOutView(APIView):
    """用户注销"""
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="用户注销成功",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        }
    )
    def post(self, request) -> Response:
        """
        处理post请求，用户注销
        :param request: post请求
        :return: Response对象，包含注销成功信息
        """
        # 获取旧token并添加到黑名单
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                auth_type, token = auth_header.split(' ', 1)
                if auth_type.lower() == 'bearer':
                    jwttoken.blacklist_token(token)
            except ValueError:
                pass

        return Response({"message": "用户注销成功"}, status=status.HTTP_200_OK)