import requests
import time

BASE_URL = "http://127.0.0.1:5000"
HEADERS = {"Authorization": "mock-token-9", "Content-Type": "application/json"}

def call_api(method, endpoint, data=None):
    url = f"{BASE_URL}{endpoint}"
    if method == "POST":
        resp = requests.post(url, headers=HEADERS, json=data)
    else:
        resp = requests.get(url, headers=HEADERS)
    if resp.status_code >= 400:
        print(f"❌ 调用 {endpoint} 失败: {resp.text}")
        return None
    return resp.json()

def main():
    print("开始初始化图谱数据...")

    # # 1. 聚类（生成大类）
    # print("正在执行聚类...（可能需要几十秒）")
    # result = call_api("POST", "/api/admin/cluster-categories", {"sample_size": 500})
    # if not result:
    #     return
    # print(f"✅ 聚类完成: {result.get('message')}")

    # # 2. 生成大类画像
    # print("正在生成大类画像...（可能需要几分钟）")
    # result = call_api("POST", "/api/admin/generate-all-category-profiles")
    # if not result:
    #     return
    # print(f"✅ 大类画像生成完成: {result.get('message')}")

    # 3. 构建图谱
    print("正在构建岗位图谱...")
    result = call_api("POST", "/api/admin/build-job-graph")
    if not result:
        return
    print(f"✅ 图谱构建完成: {result.get('message')}")

    print("\n🎉 所有步骤完成！现在你可以访问:")
    print(f"   {BASE_URL}/api/jobs/graph  查看图谱数据")
    print(f"   {BASE_URL}/api/jobs/categories  查看岗位大类")

if __name__ == "__main__":
    main()