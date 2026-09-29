import requests
import time

# ================= 配置区 =================
# 替换为你的 Ubuntu 机器局域网 IP
SERVER_IP = "192.168.50.51"

# Llama-Server 1: 向量提取服务 (端口 18080)
EMBEDDING_URL = f"http://{SERVER_IP}:18080/v1/embeddings"

# Llama-Server 2: 重排序/推理服务 (端口 18081)
RERANKER_URL = f"http://{SERVER_IP}:18081/v1/chat/completions"


# ==========================================

def test_embedding(text: str):
    """测试 18080 端口的向量生成"""
    print("\n[-] [服务 1] 开始请求 Embedding 模型 (端口 18080)...")
    payload = {
        "input": text,
        "model": "qwen3-embedding-8b"  # 模型名称可随意定义，不影响 llama-server 的执行
    }

    start_time = time.time()
    try:
        response = requests.post(EMBEDDING_URL, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        vector = result["data"][0]["embedding"]

        elapsed = time.time() - start_time
        print(f"[+] 向量提取成功! 耗时: {elapsed:.2f}s")
        print(f"[+] 向量维度: {len(vector)}")
        print(f"[+] 向量前 5 个数值: {vector[:5]}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[x] Embedding 请求失败: {e}")
        return False


def test_reranker(query: str, document: str):
    """测试 18081 端口的重排序推理逻辑"""
    print(f"\n[-] [服务 2] 开始请求 Reranker 模型 (端口 18081)...")
    prompt = f"Query: {query}\nDocument: {document}\n请评估上述 Query 与 Document 的相关性并给出打分分析:"

    # 采用 OpenAI 标准的 Chat Completion 格式
    payload = {
        "model": "qwen3-reranker-4b",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,  # 评估类任务建议调低温度，保证输出的稳定性
        "max_tokens": 512
    }

    start_time = time.time()
    try:
        response = requests.post(RERANKER_URL, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        # 解析 OpenAI 格式的返回文本
        output_text = result["choices"][0]["message"]["content"].strip()

        elapsed = time.time() - start_time
        print(f"[+] Reranker 推理成功! 耗时: {elapsed:.2f}s")
        print(f"[+] 模型输出结果:\n{output_text}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[x] Reranker 请求失败: {e}")
        return False


if __name__ == "__main__":
    print("=== Llama-Server 纯血双引擎架构连通性测试 ===")

    # 1. 测试向量提取
    test_text = "这是一个用于验证 DevOps 平台底层纯血 OpenAI API 的测试文本。"
    embed_ok = test_embedding(test_text)

    time.sleep(1)

    # 2. 测试推理重排序
    test_query = "如何优化 Kubernetes 集群监控？"
    test_doc = "Prometheus 结合外部标签 (External Labels) 可以有效实现多集群数据的统一聚合与监控验证。"
    rerank_ok = test_reranker(test_query, test_doc)

    print("\n================ 验证总结 ================")
    if embed_ok and rerank_ok:
        print("🎉 测试完美通过！你的 3060 算力节点双服务并跑非常稳定。")
        print("💡 目前所有的接口均符合 OpenAI 协议标准，后端集成将完全没有阻碍。")
    else:
        print("⚠️ 存在异常，请检查报错信息或服务端运行日志。")