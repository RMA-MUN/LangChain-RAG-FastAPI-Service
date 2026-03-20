import requests
import json

url = "http://localhost:8000/api/agent/query/stream"
headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiSDlENmlNWFNiNEN4Mm16VUozWnVRSCIsInVzZXJuYW1lIjoic3RyaW5nIiwiZW1haWwiOiJ1c2VyQGV4YW1wbGUuY29tIiwiZXhwIjoxNzc0MDc5MTAyLCJpYXQiOjE3NzM5OTI3MDIsImp0aSI6ImE4NWViOGJmLWU4NTQtNGZmOS04OTk3LTg2ZGY0ZjQzMzY3MSJ9.cbc-X8LpXH2sGlvr9ycQ3-BWJ527wC7uZ9XiMu-4seg",
    "Content-Type": "application/json"
}
data = {
    "query": "扫地机器人有哪些功能？",
    "session_id": "test_session_123"
}

print("测试流式接口...")
response = requests.post(url, headers=headers, json=data, stream=True)

if response.status_code == 200:
    print("响应状态码:", response.status_code)
    print("流式响应内容:")
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith('data:'):
                try:
                    data_part = decoded_line[5:]  # 去掉 'data: '
                    json_data = json.loads(data_part)
                    print(json_data)
                except json.JSONDecodeError:
                    print(f"无法解析JSON: {data_part}")
else:
    print(f"请求失败: {response.status_code}")
    print(response.text)