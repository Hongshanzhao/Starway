#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
职业兴趣测评功能测试脚本
使用方法：python test_assessment.py
"""

import requests
import json

BASE_URL = 'http://localhost:5000/api/assessment'

def test_get_questions():
    """测试获取测评题目"""
    print("=" * 50)
    print("测试 1: 获取测评题目 (GET /questions)")
    print("=" * 50)
    
    try:
        response = requests.get(f'{BASE_URL}/questions')
        print(f"状态码：{response.status_code}")
        
        if response.status_code == 200:
            questions = response.json()
            print(f"获取到 {len(questions)} 道题目")
            if questions:
                print(f"第一题示例：{json.dumps(questions[0], ensure_ascii=False, indent=2)}")
            return questions
        else:
            print(f"错误：{response.text}")
            return None
    except Exception as e:
        print(f"请求失败：{e}")
        return None


def test_submit_assessment(questions, test_mode=True):
    """测试提交测评答案"""
    print("\n" + "=" * 50)
    print("测试 2: 提交测评答案 (POST /submit)")
    print("=" * 50)
    
    if not questions:
        print("没有题目，跳过测试")
        return None
    
    # 构造测试答案（随机评分 1-5）
    import random
    answers = []
    for q in questions[:6]:  # 取前 6 题测试
        answers.append({
            'question_id': q['id'],
            'score': random.randint(1, 5)
        })
    
    print(f"提交答案：{json.dumps(answers, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(
            f'{BASE_URL}/submit',
            json={
                'answers': answers,
                'user_id': 1,
                'session_id': 'test_session_001',
                'test_mode': test_mode  # 测试模式不消耗 API 额度
            },
            headers={'Content-Type': 'application/json'}
        )
        print(f"状态码：{response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"提交成功！")
            print(f"结果 ID: {result.get('result_id')}")
            print(f"维度得分：{json.dumps(result.get('dimension_scores'), ensure_ascii=False, indent=2)}")
            print(f"推荐内容:\n{result.get('recommendation')}")  # 完整显示推荐内容
            return result
        else:
            print(f"错误：{response.text}")
            return None
    except Exception as e:
        print(f"请求失败：{e}")
        return None


def test_get_history(user_id=1):
    """测试获取历史记录"""
    print("\n" + "=" * 50)
    print("测试 3: 获取测评历史 (GET /history)")
    print("=" * 50)
    
    try:
        response = requests.get(f'{BASE_URL}/history/{user_id}')
        print(f"状态码：{response.status_code}")
        
        if response.status_code == 200:
            history = response.json()
            print(f"获取到 {len(history)} 条历史记录")
            if history:
                print(f"最新记录：{json.dumps(history[0], ensure_ascii=False, indent=2)}")
            return history
        else:
            print(f"错误：{response.text}")
            return None
    except Exception as e:
        print(f"请求失败：{e}")
        return None


def test_api_connection():
    """测试阿里云 API 连接"""
    print("\n" + "=" * 50)
    print("测试 4: 阿里云 API 配置检查")
    print("=" * 50)
    
    try:
        # 直接检查 .env 中的 ALIYUN_API_KEY 配置
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('ALIYUN_API_KEY')
        if not api_key or api_key == 'your-aliyun-api-key-here':
            print(f"状态码：400")
            print(f"响应：{json.dumps({'message': 'ALIYUN_API_KEY 未配置', 'status': 'error'}, ensure_ascii=False, indent=2)}")
            return False
        
        # 尝试调用阿里云百炼 API 进行简单测试
        import dashscope
        dashscope.api_key = api_key
        
        response = dashscope.Generation.call(
            model='qwen-plus',
            prompt='测试连接',
            max_tokens=10
        )
        
        if response.status_code == 200:
            print(f"状态码：200")
            print(f"响应：{json.dumps({'message': '阿里云 API 连接成功', 'status': 'success'}, ensure_ascii=False, indent=2)}")
            return True
        else:
            print(f"状态码：{response.status_code}")
            print(f"响应：{json.dumps({'message': f'阿里云 API 调用失败：{response.message}', 'status': 'error'}, ensure_ascii=False, indent=2)}")
            return False
    except Exception as e:
        print(f"请求失败：{e}")
        print(f"响应：{json.dumps({'message': str(e), 'status': 'error'}, ensure_ascii=False, indent=2)}")
        return False


def main():
    """运行所有测试"""
    print("\n🚀 开始职业兴趣测评功能测试\n")
    
    # 1. 测试 API 连接
    api_ok = test_api_connection()
    
    # 2. 获取题目
    questions = test_get_questions()
    
    # 3. 提交答案（先用测试模式）
    result = test_submit_assessment(questions, test_mode=True)
    
    # 4. 获取历史
    history = test_get_history(user_id=1)
    
    # 5. 【新增】测试正式模式（调用 LLM API）
    print("\n" + "=" * 50)
    print("测试 5: 正式模式测试 (调用阿里云 LLM)")
    print("=" * 50)
    print("⚠️  此测试会消耗 API 额度，请确认配置正确")
    result_formal = test_submit_assessment(questions, test_mode=False)
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试总结")
    print("=" * 50)
    print(f"API 连接：{'✅ 成功' if api_ok else '❌ 失败'}")
    print(f"获取题目：{'✅ 成功' if questions else '❌ 失败'}")
    print(f"提交答案 (测试模式):{'✅ 成功' if result else '❌ 失败'}")
    print(f"提交答案 (正式模式):{'✅ 成功' if result_formal else '❌ 失败'}")
    print(f"获取历史：{'✅ 成功' if history else '❌ 失败'}")
    
    if all([questions, result, history]):  # 正式模式可选，不影响整体测试
        print("\n🎉 所有测试通过！可以正式使用了")
    else:
        print("\n⚠️ 部分测试失败，请检查配置")
    
    # 提供直接访问的 URL
    print("\n" + "=" * 50)
    print("🌐 直接访问 URL 测试")
    print("=" * 50)
    print(f"获取题目：{BASE_URL}/questions")
    print(f"获取历史：{BASE_URL}/history/1")
    print(f"\n提交答案需要使用 POST 请求，可用以下 curl 命令测试：")
    print(f"""
curl -X POST {BASE_URL}/submit \\
  -H "Content-Type: application/json" \\
  -d '{{"answers":[{{"question_id":1,"score":5}}], "user_id":1, "test_mode":true}}'
    """)


if __name__ == '__main__':
    main()