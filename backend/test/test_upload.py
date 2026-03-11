import requests

# 测试上传 PDF 文件
print("测试上传 PDF 文件...")
url = "http://localhost:8000/api/vector/add"
files = {'file': open('data/扫地机器人100问.pdf', 'rb')}
response = requests.post(url, files=files)
print(f"状态码: {response.status_code}")
print(f"响应内容: {response.json()}")
print()

# 测试上传 TXT 文件
print("测试上传 TXT 文件...")
files = {'file': open('data/扫地机器人100问2.txt', 'rb')}
response = requests.post(url, files=files)
print(f"状态码: {response.status_code}")
print(f"响应内容: {response.json()}")
print()

# 测试上传不支持的文件类型
print("测试上传不支持的文件类型...")
files = {'file': open('data/external/records.csv', 'rb')}
response = requests.post(url, files=files)
print(f"状态码: {response.status_code}")
print(f"响应内容: {response.json()}")
