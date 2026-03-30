from sentence_transformers import CrossEncoder
import torch

# 本地重排序模型路径
LOCAL_MODEL_PATH = r"D:\Hugging_Face\models\Qwen3-Reranker-0.6B"

print(f"✅ 加载本地重排序模型：{LOCAL_MODEL_PATH}")

device="cuda" if torch.cuda.is_available() else "cpu"

# 构建本地模型
model = CrossEncoder(
    LOCAL_MODEL_PATH,
    max_length=512,
    device=device,
    local_files_only=True
)

QUERY = "如何在FastAPI中实现RAG系统的重排序功能"
DOCUMENTS = [
    "FastAPI中可以使用Qwen3-Reranker模型实现RAG系统的重排序功能，提升检索精度",
    "在FastAPI应用中集成重排序模型需要先加载模型，然后对检索结果进行评分排序",
    "RAG系统的重排序步骤通常在检索之后、生成之前进行，用于优化上下文质量",
    "FastAPI是一个高性能的Python Web框架，适合构建AI应用和API服务",
    "Qwen3-Reranker-0.6B是阿里巴巴推出的轻量化中文重排序模型，适合部署在各类应用中"
]

# 构造查询+文档对
pairs = [(QUERY, doc) for doc in DOCUMENTS]

# batch_size=1，避免padding令牌报错
scores = model.predict(pairs, batch_size=1)

# 按相关性分数排序
results = [{"document": doc, "score": float(score)} for doc, score in zip(DOCUMENTS, scores)]
sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)

# 输出最终结果
print("="*80)
print(f"使用设备：{device}")
print(f"🔍 查询：{QUERY}")
print("="*80)
for idx, item in enumerate(sorted_results, 1):
    print(f"🏆 排名 {idx} | 相关性分数：{item['score']:.4f}")
    print(f"📄 内容：{item['document']}\n")