# Hugging Face 模型下载配置

## 模型介绍

Qwen3-Reranker-0.6B 是阿里巴巴推出的轻量化中文重排序模型，专为中文文本相关性排序设计：
- **轻量级**：仅0.6B参数，适合本地部署
- **高性能**：能够准确评估查询与文档的相关性
- **中文优化**：针对中文文本进行了特别优化

## 安装步骤

### 1. 安装依赖包

```bash
# 进入后端目录
cd backend

# 安装重排序模型依赖
uv add sentence-transformers torch
```

### 2. 模型获取方式

#### 方法一：自动下载（推荐）

系统支持自动检测和下载模型。当FastAPI服务器启动时：
1. 自动检查配置的模型路径是否存在
2. 如果不存在，自动从Hugging Face下载模型到指定路径
3. 下载完成后在第一次使用时自动加载

**无需手动下载**，系统会在服务器启动时自动完成检查和下载。

#### 方法二：手动从Hugging Face下载

如果需要手动下载：
1. 访问模型页面：[Qwen/Qwen3-Reranker-0.6B](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B)
2. 下载完整模型文件到本地目录，推荐路径：
   ```
   D:\Hugging_Face\models\Qwen3-Reranker-0.6B
   ```

## 环境变量配置

在 `.env` 文件中配置模型路径：

```env
# 重排序模型配置（可选）
RERANKER_MODEL_PATH=D:\Hugging_Face\models\Qwen3-Reranker-0.6B
```

## 测试重排序功能

项目提供了测试脚本 `test_reorder.py`，可以用来验证模型安装是否成功：

```bash
cd backend
python test_reorder.py
```

成功输出示例：
```
✅ 加载本地重排序模型：D:\Hugging_Face\models\Qwen3-Reranker-0.6B
✅ 模型加载成功，使用设备：cuda
================================================================================
使用设备：cuda
🔍 查询：如何在FastAPI中实现RAG系统的重排序功能
================================================================================
🏆 排名 1 | 相关性分数：2.1234
📄 内容：FastAPI中可以使用Qwen3-Reranker模型实现RAG系统的重排序功能，提升检索精度

🏆 排名 2 | 相关性分数：1.8765
📄 内容：在FastAPI应用中集成重排序模型需要先加载模型，然后对检索结果进行评分排序
```

## API调用示例

重排序功能已集成到系统的 `/api/reorder` 端点：

```python
import requests

# API调用示例
payload = {
    "query": "如何实现RAG系统",
    "documents": [
        "FastAPI中可以使用Qwen3-Reranker模型实现RAG系统的重排序功能",
        "RAG系统需要向量数据库来存储文档嵌入",
        "重排序是提升RAG系统准确性的关键步骤"
    ]
}

response = requests.post("http://localhost:8000/api/reorder", json=payload)
result = response.json()
print(result)
```

## 环境要求

### 硬件要求
- **CPU模式**：任意现代CPU
- **GPU模式**：支持CUDA的NVIDIA GPU（推荐，大幅提升性能）

### 软件要求
- Python 3.8+
- PyTorch 2.0+
- sentence_transformers 2.2.0+

## 性能优化建议

1. **GPU加速**：确保安装了CUDA版本的PyTorch以获得最佳性能
2. **批量处理**：虽然当前设置 `batch_size=1` 避免padding错误，但在文档数量较少时可以尝试增加批次大小
3. **模型缓存**：模型会在服务启动时加载一次，后续请求无需重新加载

## 版本信息

- 模型版本：Qwen3-Reranker-0.6B
- sentence-transformers：2.2.0+
- PyTorch：2.0+