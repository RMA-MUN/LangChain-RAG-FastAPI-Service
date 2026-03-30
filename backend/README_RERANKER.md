# Qwen3-Reranker-0.6B 重排序模型安装指南

## 模型介绍

Qwen3-Reranker-0.6B 是阿里巴巴推出的轻量化中文重排序模型，专为中文文本相关性排序设计，具有以下特点：
- 轻量级：仅0.6B参数，适合本地部署
- 高性能：能够准确评估查询与文档的相关性
- 中文优化：针对中文文本进行了特别优化

## 安装步骤

### 1. 安装依赖包

在项目根目录下运行以下命令安装所需的Python依赖：

```bash
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
3. 确保下载包含以下文件：
   - config.json
   - model.safetensors
   - tokenizer.json
   - tokenizer_config.json
   - vocab.txt

#### 方法三：使用Python脚本下载

```python
from sentence_transformers import CrossEncoder

# 自动下载并缓存模型
model = CrossEncoder("Qwen/Qwen3-Reranker-0.6B")
```

### 3. 配置模型路径

修改 `.env` 文件中的模型路径配置：

```
# 重排序模型配置
RERANKER_MODEL_PATH=D:\Hugging_Face\models\Qwen3-Reranker-0.6B
```

确保该路径与你希望保存模型的位置一致。如果路径不存在，系统会自动创建并下载模型。

## 环境要求

### 硬件要求
- **CPU模式**：任意现代CPU
- **GPU模式**：支持CUDA的NVIDIA GPU（推荐，大幅提升性能）

### 软件要求
- Python 3.8+
- PyTorch 2.0+
- sentence_transformers 2.2.0+

## 使用说明

### 测试重排序功能

项目根目录提供了测试脚本 `test_reorder.py`，可以用来验证模型安装是否成功：

```bash
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

### API调用示例

重排序功能已集成到系统的 `/api/chat/reorder` 端点：

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

response = requests.post("http://localhost:8000/api/chat/reorder", json=payload)
result = response.json()
print(result)
```

## 常见问题

### 1. 模型加载失败

**问题**：`RuntimeError: 重排序模型加载失败: [Errno 2] No such file or directory`

**解决方法**：
- 检查模型路径是否正确
- 确保模型文件完整下载
- 检查文件权限

### 2. CUDA内存不足

**问题**：`CUDA out of memory`

**解决方法**：
- 降低 `max_length` 参数（默认为512）
- 减小 `batch_size`（当前设置为1）
- 使用CPU模式：在 `reorder_service.py` 中将 `device` 强制设置为 `"cpu"`

### 3. 依赖安装失败

**问题**：安装 `sentence-transformers` 或 `torch` 失败

**解决方法**：
- 更新pip：`pip install --upgrade pip`
- 使用镜像源：`pip install sentence-transformers torch -i https://pypi.tuna.tsinghua.edu.cn/simple`

## 性能优化建议

1. **GPU加速**：确保安装了CUDA版本的PyTorch以获得最佳性能
2. **批量处理**：虽然当前设置 `batch_size=1` 避免padding错误，但在文档数量较少时可以尝试增加批次大小
3. **模型缓存**：模型会在服务启动时加载一次，后续请求无需重新加载

## 版本信息

- 模型版本：Qwen3-Reranker-0.6B
- sentence-transformers：2.2.0+
- PyTorch：2.0+

## 故障排除

如果遇到其他问题，请检查：
1. 查看应用日志（位于 `logs/` 目录）
2. 验证模型文件完整性
3. 确认Python环境依赖正确安装

## 联系支持

如有问题，可提交issue或联系作者