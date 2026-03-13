# UserService API 文档

## 接口列表

### 1. 注册接口

**URL**: `/api/auth/register/`
**方法**: `POST`
**描述**: 用户注册接口，创建新用户

#### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| user_name | string | 是 | 用户名 |
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码，至少6位 |
| password2 | string | 是 | 确认密码，必须与password一致 |
| phone | string | 否 | 手机号，11位 |

#### 响应参数

| 参数名 | 类型 | 描述 |
|--------|------|------|
| code | integer | 状态码，成功为200 |
| message | string | 响应消息 |
| data | object | 响应数据 |
| data.user | object | 用户信息 |
| data.user.user_id | string | 用户唯一ID（UUID） |
| data.user.user_name | string | 用户名 |
| data.user.email | string | 邮箱地址 |
| data.user.avatar | string | 头像URL，可能为null |
| data.user.date_joined | string | 注册时间（ISO格式） |

#### 请求示例

```json
{
  "user_name": "testuser",
  "email": "test@example.com",
  "password": "password123",
  "password2": "password123",
  "phone": "13800138000"
}
```

#### 响应示例

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "user": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_name": "testuser",
      "email": "test@example.com",
      "avatar": null,
      "date_joined": "2026-03-13T14:42:13Z"
    }
  }
}
```

### 2. 登录接口

**URL**: `/api/auth/login/`
**方法**: `POST`
**描述**: 用户登录接口，获取访问令牌

#### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码 |

#### 响应参数

| 参数名 | 类型 | 描述 |
|--------|------|------|
| access | string | 访问令牌，用于调用需要认证的接口 |
| refresh | string | 刷新令牌，用于获取新的访问令牌 |

#### 请求示例

```json
{
  "email": "test@example.com",
  "password": "password123"
}
```

#### 响应示例

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 3. 刷新令牌接口

**URL**: `/api/auth/token/refresh/`
**方法**: `POST`
**描述**: 使用刷新令牌获取新的访问令牌

#### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| refresh | string | 是 | 刷新令牌 |

#### 响应参数

| 参数名 | 类型 | 描述 |
|--------|------|------|
| access | string | 新的访问令牌 |

#### 请求示例

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### 响应示例

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 4. 获取用户信息接口

**URL**: `/api/auth/profile/`
**方法**: `GET`
**描述**: 获取当前登录用户的详细信息
**认证**: 需要在请求头中携带 `Authorization: Bearer <access_token>`

#### 请求参数

无

#### 响应参数

| 参数名 | 类型 | 描述 |
|--------|------|------|
| user_id | string | 用户唯一ID（UUID） |
| user_name | string | 用户名 |
| email | string | 邮箱地址 |
| avatar | string | 头像URL，可能为null |
| date_joined | string | 注册时间（ISO格式） |

#### 请求示例

```
GET /api/auth/profile/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 响应示例

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_name": "testuser",
  "email": "test@example.com",
  "avatar": null,
  "date_joined": "2026-03-13T14:42:13Z"
}
```

## 认证方式

所有需要认证的接口（如获取用户信息）都需要在请求头中携带 JWT 访问令牌：

```
Authorization: Bearer <access_token>
```

其中 `<access_token>` 是通过登录接口获取的访问令牌。

## 错误响应格式

当请求失败时，返回的错误响应格式如下：

```json
{
  "code": 400,
  "message": "错误信息",
  "data": null
}
```

## 注意事项

1. 密码长度至少为6位
2. 邮箱必须是有效的邮箱格式
3. 手机号必须是11位数字
4. 所有需要认证的接口必须携带有效的访问令牌
5. 访问令牌过期后，需要使用刷新令牌获取新的访问令牌