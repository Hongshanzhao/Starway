"""
services/llm_service.py
大模型服务总模块（职业规划AI核心）

功能定位：
  本文件是整个系统**AI能力的统一出口**，集成大模型调用、简历解析、岗位推荐、
  职业规划生成、问答对话、岗位画像自动构建、职业路径图谱生成等全功能。
  所有需要AI智能的业务都会调用这里。

核心能力：
  1. 大模型统一调度：支持本地模板降级 + DeepSeek + 阿里云百炼（通义千问）
  2. 简历智能解析：从文本提取技能、证书、经历、竞争力
  3. 岗位智能推荐：基于学生画像做匹配度计算与排序
  4. 职业规划生成：自动生成学习路径、提升方案、发展建议
  5. 智能问答对话：支持职业咨询、岗位咨询、规划咨询
  6. 岗位画像自动化：批量生成岗位技能/证书/软实力要求
  7. 职业路径图谱：自动生成晋升路径（垂直）+ 转岗路径（横向）
  8. 技能归一化、同义词合并、文本相似度计算

外部依赖：
  - 数据库：job / job_categories / job_profile / job_relations
  - 大模型：DeepSeek / 阿里云百炼 API
  - 工具：jieba分词、requests、dashscope
  - 配置：API_KEY、LLM_MODE、LLM_MAX_CALLS_PER_RUN

设计特点：
  - 自动重试与限流保护
  - 流式输出支持（用于报告生成）
  - 同义词合并、软能力标准化
  - 岗位分类、画像、图谱全自动构建

废弃/备注：
  - 原智谱AI代码已保留注释，可随时切回
  - 部分算法模块来自 deprecated 目录，仅做兼容兜底
  - 大模型调用带次数限制，防止测试刷额度
"""
import os
import json
import time
import logging
from typing import Dict, Any, List, Optional
from backend.deprecated.algorithms import recommend_jobs, compute_match_score

# 配置日志，确保在测试中也能看到输出
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 高级算法类（若存在则优先使用）
try:
    from backend.deprecated.career_ml import CareerRecommend
except Exception:
    CareerRecommend = None


def _get_deepseek_key():
    """✅ 动态获取 API Key，确保 load_dotenv 后生效"""
    return os.environ.get('DEEPSEEK_API_KEY')


def _call_deepseek(prompt: str) -> str:
    """调用 DeepSeek HTTP 接口（兼容 OpenAI-style chat completion）"""
    api_key = _get_deepseek_key()
    if not api_key:
        print('⚠️ DEEPSEEK_API_KEY 未配置，使用本地模板')
        return ''
    try:
        import requests
        url = 'https://api.siliconflow.cn/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': 'deepseek-ai/DeepSeek-V3',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 6000
        }
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        j = r.json()
        # 兼容多种返回结构
        if 'choices' in j and len(j['choices']) > 0:
            c = j['choices'][0]
            if isinstance(c.get('message'), dict) and 'content' in c['message']:
                return c['message']['content']
            if 'text' in c:
                return c['text']
        return j.get('result') or ''
    except Exception as e:
        print(f'❌ DeepSeek 调用失败：{e}')
        return ''


def parse_resume(file_path: str) -> Dict[str, Any]:
    """解析简历（演示版）"""
    try:
        _, ext = os.path.splitext(file_path.lower())
        if ext in ('.txt', '.md'):
            with open(file_path, 'r', encoding='utf-8') as f:
                txt = f.read()
            skills = []
            for line in txt.splitlines():
                if ':' in line:
                    k, v = line.split(':', 1)
                    if k.strip().lower() in ('skills', '技能'):
                        skills = [s.strip() for s in v.split(',') if s.strip()]
            return {
                'name': None,
                'major': None,
                'grade': None,
                'skills': skills or ['Python'],
                'certificates': [],
                'internships': None,
                'interests': [],
                'completeness': 70,
                'competitiveness': 60
            }
    except Exception:
        pass

    return {
        'name': '测试学生',
        'major': '计算机',
        'grade': '大三',
        'skills': ['Python', 'SQL'],
        'certificates': [],
        'internships': None,
        'interests': ['数据分析'],
        'completeness': 80,
        'competitiveness': 70
    }


def intelligent_recommendation(student: Dict[str, Any], jobs: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
    """返回推荐岗位列表以及每个岗位的匹配详情"""
    if CareerRecommend is not None:
        try:
            cr = CareerRecommend()
            recs_raw = cr.get_match_list(student, jobs, top_k=top_n)
            out = []
            for r in recs_raw:
                out.append({'job': r['job'], 'match': {'overall_score': r['score'], 'skill_score': r.get('skill_score')}})
            return out
        except Exception:
            pass

    recs = recommend_jobs(student, jobs, top_n)
    out = []
    for job, detail in recs:
        item = {'job': job, 'match': detail}
        out.append(item)
    return out


def generate_plan_suggestion(student: Dict[str, Any], job_name: str) -> str:
    """基于学生信息生成规划建议文本（模板 + 可选大模型增强）"""
    template = []
    template.append(f"目标岗位：{job_name}")
    template.append("总体建议：")
    template.append("1. 技能提升：根据岗位需求补齐关键技能，例如掌握相关框架与工具。")
    template.append("2. 项目经验：建议完成至少 1-2 个相关项目，展示端到端能力。")
    template.append("3. 简历优化：将关键技能与项目成果量化展示，突出业绩与指标。")
    template.append("4. 面试准备：整理常见技术问题与行为问题的回答要点。")

    prompt = '\n'.join(template) + '\n\n学生信息：' + json.dumps(student, ensure_ascii=False)
    
    print('🔍 正在调用 DeepSeek 生成规划建议...')
    ai = _call_deepseek(prompt)
    if ai:
        print('✅ DeepSeek 调用成功')
        return ai
    print('⚠️ DeepSeek 调用失败，使用本地模板')
    return '\n'.join(template)


def chat_qa(question: str, context: str = '') -> str:
    """简洁的问答接口"""
    api_key = _get_deepseek_key()
    if api_key:
        print('🔍 正在调用 DeepSeek 回答问答...')
        out = _call_deepseek(f"Q: {question}\n上下文：{context}")
        if out:
            print('✅ DeepSeek 问答成功')
            return out

    q = question.lower()
    if '如何' in q or '怎样' in q:
        return '要提升核心技能，建议系统学习相关课程、实践项目并通过线上平台参与挑战。'
    if '工资' in q or '薪资' in q:
        return '薪资受地区、公司规模、经验影响，建议参考同行业招聘信息并结合自身技能评估。'
    return '这是一个很好的问题，建议您提供更多背景（例如兴趣、技能、期望行业），我可以给出更具体建议。'

# ==================== 以下是你新增的智谱 API 相关函数（已替换为阿里云百炼）====================
import json
import re
import time
from typing import Optional, Dict, Any, List, Tuple

# 阿里云百炼 SDK
import dashscope
# 确保 config.py 中定义了 ALIYUN_API_KEY，或者从环境变量直接读取
from config import ALIYUN_API_KEY, LLM_MODE, LLM_FORCE_REAL, LLM_MAX_CALLS_PER_RUN

# 设置阿里云 API Key（全局设置）
# 备注：LLM_MODE=local 时不会实际调用外部API
if ALIYUN_API_KEY:
    dashscope.api_key = ALIYUN_API_KEY
else:
    # 尝试直接从环境变量读取作为备用
    import os
    key = os.getenv('ALIYUN_API_KEY')
    if key:
        dashscope.api_key = key

# 内存计数器，避免一次测试/运行中无限制刷API
_llm_call_count = 0


def _local_llm_fallback(prompt: str) -> str:
    """本地模板生成，供无API密钥或API调用失败时使用"""
    
    import re
    
    # 1. 尝试从 prompt 中提取岗位名称
    job_match = re.search(r'【(.*?)】', prompt)
    job_name = job_match.group(1) if job_match else "目标岗位"
    
    # 2. 尝试提取学生技能
    skills = []
    tech_keywords = ['Python', 'Java', 'JavaScript', 'Vue', 'React', 'SQL', 'HTML', 'CSS', 
                     'Spring', 'Django', 'Flask', 'TensorFlow', 'PyTorch', 'C++', 'C#', 
                     'PHP', 'Go', 'Rust', 'Swift', 'Kotlin', 'Node.js', 'TypeScript',
                     '数据分析', '机器学习', '深度学习', '前端开发', '后端开发', '全栈']
    
    for kw in tech_keywords:
        if kw.lower() in prompt.lower():
            skills.append(kw)
    
    skills_text = "、".join(skills[:5]) if skills else "相关技术"

    # 3. 返回完整的模板报告
    return f"""# 职业生涯发展报告（本地演示版）

> ⚠️ 提示：当前未配置阿里云百炼 API Key，本报告使用本地模板生成。  
> 配置 `ALIYUN_API_KEY` 后即可获得 AI 个性化报告。

## 一、自我认知总结

根据您的能力画像，您在专业技能、学习能力方面表现良好。建议进一步明确职业兴趣方向，结合【{job_name}】岗位要求制定发展计划。

## 二、人岗匹配分析

### 2.1 核心优势
- 具备良好的学习能力和技术基础（{skills_text}）
- 有相关项目实践经验
- 软能力评分良好，适合团队协作

### 2.2 待提升方向
- 补充【{job_name}】岗位的核心技能
- 增加相关实习经历
- 考取行业认可证书

## 三、职业发展路径

### 3.1 晋升路径
初级{job_name} → 中级{job_name} → 高级{job_name} → 技术专家/架构师

### 3.2 转型方向
可考虑向产品经理、技术架构师、技术管理等方向发展

## 四、分阶段行动计划

### 短期（1年内）
- 掌握【{job_name}】核心技能框架
- 完成 1-2 个相关项目
- 准备求职作品集

### 中期（1-3年）
- 积累项目经验，提升技术深度
- 考取行业相关证书
- 建立技术影响力

### 长期（3-5年）
- 成为领域专家或技术负责人
- 具备跨团队协作和项目管理能力

## 五、评估与调整建议

建议每 6 个月进行一次自我评估，根据行业发展和个人成长调整规划。

---
*本报告由系统本地模板生成。配置阿里云百炼 API Key 后即可获得 AI 个性化报告。*
"""


def call_llm(prompt: str, temperature=0.3, max_tokens=6000, thinking=False, max_retries=1) -> str:
    """
    统一 LLM 调用入口。
    【优化】默认 max_retries 降为 1，避免测试时长时间等待；增加详细日志。
    """
    global _llm_call_count
    
    start_time = time.time()
    logger.info(f"🚀 [LLM Call] 开始调用 | 模式：{LLM_MODE} | 强制真实：{LLM_FORCE_REAL}")
    logger.info(f"📝 [Prompt Preview] {prompt[:100]}... (总长：{len(prompt)})")

    if LLM_FORCE_REAL:
        result = _call_zhipu(prompt, temperature, max_tokens, thinking, max_retries)
    else:
        _llm_call_count += 1
        if _llm_call_count > LLM_MAX_CALLS_PER_RUN:
            logger.warning(f"⚠️ 达到本次运行 LLM 调用上限 ({LLM_MAX_CALLS_PER_RUN})，使用本地降级。")
            result = _local_llm_fallback(prompt)
        elif LLM_MODE == 'local':
            logger.info("⚠️ LLM_MODE=local，使用本地降级内容。")
            result = _local_llm_fallback(prompt)
        elif dashscope.api_key:
            result = _call_zhipu(prompt, temperature, max_tokens, thinking, max_retries)
        else:
            logger.warning("⚠️ 未配置阿里云 API Key，使用本地降级内容。")
            result = _local_llm_fallback(prompt)

    elapsed = time.time() - start_time
    res_len = len(result) if result else 0
    logger.info(f"✅ [LLM Done] 耗时：{elapsed:.2f}s | 返回字符数：{res_len}")
    
    if res_len > 0:
        logger.debug(f"📄 [Response Preview] {result[:200]}...")
        
    return result


def _call_zhipu(prompt: str, temperature=0.3, max_tokens=6000, thinking=False, max_retries=1) -> str:
    """
    【真实实现】调用阿里云百炼 qwen-plus 模型。
    【优化】增加每次重试的日志，明确失败原因。
    """
    if not dashscope.api_key:
        logger.error("❌ 错误：阿里云 API Key (ALIYUN_API_KEY) 未配置，无法调用大模型。")
        return ""

    for attempt in range(max_retries):
        try:
            logger.info(f"🔄 正在调用阿里云 API (尝试 {attempt+1}/{max_retries})...")
            response = dashscope.Generation.call(
                model='qwen-plus',
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.7,
            )
            
            if response.status_code == 200:
                result = response.output.text
                logger.info(f"✅ 阿里云调用成功，返回 {len(result)} 字符")
                return result
            else:
                logger.error(f"❌ 阿里云调用失败：{response.code} - {response.message}")
                if "429" in str(response) or "throttling" in str(response).lower():
                    wait_time = (attempt + 1) * 2  # 缩短等待时间
                    logger.warning(f"⚠️ 触发限流，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    return ""
        except Exception as e:
            logger.error(f"❌ 阿里云调用异常：{e}")
            if "429" in str(e) or "rate" in str(e).lower():
                wait_time = (attempt + 1) * 2
                logger.warning(f"⚠️ 触发限流，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                return ""
    
    logger.error("❌ 阿里云调用重试耗尽，返回空字符串")
    return ""

# 如果你以后想切换回智谱，可以将上面的 _call_zhipu 替换为以下注释掉的代码：
# from zhipuai import ZhipuAI
# _zhipu_client = None
# def _get_zhipu_client():
#     global _zhipu_client
#     if _zhipu_client is None:
#         _zhipu_client = ZhipuAI(api_key=ZHIPU_API_KEY)
#     return _zhipu_client
# def _call_zhipu(prompt: str, temperature=0.3, max_tokens=2000, thinking=False, max_retries=3) -> str:
#     for attempt in range(max_retries):
#         try:
#             client = _get_zhipu_client()
#             params = {
#                 "model": "glm-4-flash",
#                 "messages": [{"role": "user", "content": prompt}],
#                 "temperature": temperature,
#                 "max_tokens": max_tokens,
#                 "top_p": 0.7,
#             }
#             if thinking:
#                 params["thinking"] = {"type": "enabled"}
#             response = client.chat.completions.create(**params)
#             return response.choices[0].message.content
#         except Exception as e:
#             error_str = str(e)
#             if "429" in error_str or "rate limit" in error_str.lower():
#                 wait_time = (attempt + 1) * 5
#                 print(f"⚠️ 智谱速率限制，等待 {wait_time} 秒后重试 (尝试 {attempt+1}/{max_retries})...")
#                 time.sleep(wait_time)
#             else:
#                 print(f"❌ 智谱 API 调用失败（非限流错误）：{e}")
#                 return ""
#     print("❌ 智谱 API 调用重试耗尽，返回空字符串")
#     return ""

# ---------- 分词相似度相关（用于分类） ----------
try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    print("⚠️ 警告: jieba 未安装，将使用简单的子串匹配进行岗位分类，准确性可能较低。建议安装 jieba: pip install jieba")

def _calc_text_similarity(text1: str, text2: str) -> float:
    """计算两个文本的分词相似度（Jaccard相似度），若jieba不可用则回退到子串包含判断"""
    if not JIEBA_AVAILABLE:
        return 1.0 if text1 in text2 or text2 in text1 else 0.0
    words1 = set(jieba.cut(text1))
    words2 = set(jieba.cut(text2))
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union)

# 流式
def call_llm_stream(prompt: str, temperature=0.7, max_tokens=8000):
    """
    阿里云百炼流式调用，每次 yield 一个**增量**文本块。
    """
    import dashscope
    from config import ALIYUN_API_KEY
    if ALIYUN_API_KEY:
        dashscope.api_key = ALIYUN_API_KEY

    if not dashscope.api_key:
        logger.error("❌ 阿里云 API Key 未配置，无法使用流式调用")
        yield "报告生成失败：未配置 API Key"
        return

    try:
        responses = dashscope.Generation.call(
            model='qwen-plus',
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            result_format='message'
        )
        previous_text = ""
        for resp in responses:
            if resp.output and resp.output.choices:
                chunk = resp.output.choices[0].message.content
                if chunk:
                    # 只返回增量部分
                    if chunk.startswith(previous_text):
                        new_part = chunk[len(previous_text):]
                    else:
                        # 如果 chunk 不是累积的，直接返回
                        new_part = chunk
                    previous_text = chunk
                    if new_part:
                        yield new_part
    except Exception as e:
        logger.error(f"流式调用失败：{e}")
        yield f"报告生成失败：{str(e)}"

# ---------- 技能合并辅助函数 ----------
def _merge_skills(skills_list: List[str]) -> List[str]:
    """
    对技能列表进行去重、合并同义词，返回标准化后的列表。
    同义词映射可根据实际数据扩展。
    """
    skill_alias = {
        "HTML5": "HTML",
        "CSS3": "CSS",
        "Vue3.0": "Vue",
        "Vue2": "Vue",
        "React.js": "React",
        "AngularJS": "Angular",
        "Angular2": "Angular",
        "Angular 2+": "Angular",
        "TypeScript": "TS",
        "Javascript": "JavaScript",
        "ES6": "JavaScript（ES6）",
        "ES2015": "JavaScript（ES6）",
        "Node.js": "NodeJS",
        "Express.js": "Express",
        "Mysql": "MySQL",
        "Sql Server": "SQL Server",
        "Photoshop": "PS",
        "Illustrator": "AI",
        "Figma": "Figma",
        "Sketch": "Sketch",
        "Axure RP": "Axure",
        # 可以继续添加
    }
    cleaned = []
    seen = set()
    for skill in skills_list:
        # 去除前后空格
        skill = skill.strip()
        if not skill:
            continue
        # 标准化
        normalized = skill_alias.get(skill, skill)
        # 去重
        if normalized not in seen:
            seen.add(normalized)
            cleaned.append(normalized)
    return cleaned

# ========== 第一步：自动聚类，生成大类（优化版） ==========
def cluster_categories_with_zhipu(sample_size: int = 500) -> List[Dict[str, Any]]:
    """
    从数据库中随机抽取 sample_size 条岗位数据（默认500），调用大模型分析，
    返回10-15个大类，每个大类包含名称和该大类下的职位名称列表。
    """
    from db import get_db
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT job_name, job_description FROM job
        WHERE job_description IS NOT NULL AND job_description != ''
        ORDER BY RANDOM() LIMIT ?
    """, (sample_size,))
    samples = cursor.fetchall()
    conn.close()

    if not samples:
        return []

    sample_text = ""
    for i, row in enumerate(samples, 1):
        desc = row['job_description'][:200] if row['job_description'] else "无描述"
        sample_text += f"{i}. 岗位名称：{row['job_name']}\n   岗位描述：{desc}...\n\n"

    prompt = f"""
你是一个职业分类专家。下面有{sample_size}条岗位数据样本（包含岗位名称和部分描述）。请根据这些岗位的核心技能和要求，将它们归纳为10-15个主要大类。
要求：
- 每个大类应有一个概括性的名称，例如“后端开发类”、“前端开发类”、“数据科学类”等。
- 每个大类下列出该大类包含的典型职位名称（从样本中观察到的，或归纳出的职位名称），列表应尽量完整，覆盖常见岗位变体。
- 返回严格的JSON格式，是一个数组，每个元素包含：
  {{
    "category_name": "大类名称",
    "job_titles": ["职位名称1", "职位名称2", ...]
  }}
- 确保大类数量在10-15之间。
- 只返回JSON，不要其他文字。

样本数据：
{sample_text}
"""
    for attempt in range(2):
        result = _call_zhipu(prompt, temperature=0.2, max_tokens=6000)
        if not result:
            continue
        json_match = re.search(r'```json\n(.*?)\n```', result, re.DOTALL)
        if json_match:
            result = json_match.group(1)
        try:
            categories = json.loads(result)
            if isinstance(categories, list):
                return categories
            else:
                print(f"返回的JSON不是数组，尝试重试...")
        except Exception as e:
            print(f"解析聚类结果失败（尝试 {attempt+1}）：{e}")
    return []

# ========== 第二步：为每个岗位分配大类（基于分词相似度） ==========
def assign_categories_by_keywords(category_job_titles_map: Dict[str, List[str]], similarity_threshold: float = 0.3):
    """
    根据聚类得到的大类-职位名称映射，为job表中的每个岗位分配category_id。
    使用分词相似度计算岗位名称与职位标题的匹配程度，选择相似度最高的类别。
    如果没有匹配（最高相似度 < threshold），则category_id保持NULL。
    """
    from db import get_db
    conn = get_db()
    cursor = conn.cursor()

    # 获取所有大类ID和名称
    cursor.execute("SELECT id, name FROM job_categories")
    cat_id_map = {row['name']: row['id'] for row in cursor.fetchall()}

    # 获取所有未分类的岗位
    cursor.execute("SELECT rowid, job_name FROM job WHERE category_id IS NULL")
    jobs = cursor.fetchall()
    count = 0
    for job in jobs:
        job_id = job['rowid']
        job_name = job['job_name']
        best_cat_id = None
        best_score = 0.0
        for cat_name, titles in category_job_titles_map.items():
            for title in titles:
                if not title:
                    continue
                score = _calc_text_similarity(job_name, title)
                if score > best_score:
                    best_score = score
                    best_cat_id = cat_id_map.get(cat_name)
        if best_score >= similarity_threshold and best_cat_id:
            cursor.execute("UPDATE job SET category_id = ? WHERE rowid = ?", (best_cat_id, job_id))
            conn.commit()
            count += 1
    conn.close()
    return count

# ========== 第三步：为每个大类生成通用画像（优化版） ==========
# ========== 第三步：为每个大类生成通用画像（优化版） ==========
def generate_category_profile_with_zhipu(category_id: int) -> bool:
    from db import get_db
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM job_categories WHERE id = ?", (category_id,))
    cat = cursor.fetchone()
    if not cat:
        conn.close()
        return False
    category_name = cat['name']

    # 随机抽取50条描述（提高代表性）
    cursor.execute(
        "SELECT job_description FROM job WHERE category_id = ? AND job_description IS NOT NULL ORDER BY RANDOM() LIMIT 50",
        (category_id,)
    )
    descs = [row['job_description'] for row in cursor.fetchall() if row['job_description']]
    if not descs:
        conn.close()
        return False

    combined = "\n---\n".join(descs)
    prompt = f"""
你是一个职业分析师。请根据以下属于"{category_name}"的多个岗位描述，提炼该大类岗位的通用画像。
要求返回严格的JSON格式，包含：
- skills：技能列表，**请合并相似技能**（例如 HTML 和 HTML5 合并为 HTML，Vue 和 Vue3.0 合并为 Vue），并按重要性或出现频率排序。如果可能，请按类别组织技能（例如基础技术、框架与库、工具与工程化、数据库等），但最终仍以字符串列表形式返回（可在技能名称后加括号注明分类，如“HTML（基础技术）”），或者直接返回列表即可。
- certificates：常见证书要求（字符串数组）。
- soft_abilities：软实力要求，对象形式，键为软能力名称，值为包含 `score`（1-5分）和 `description`（详细描述该能力在岗位中的具体体现）的对象。
  请根据岗位描述提炼出最相关的软能力，至少应包含创新能力、学习能力、抗压能力、沟通能力、实习能力（如果这些能力在描述中有体现，请给出评分和描述；如果某个能力完全未提及，可给出默认值，但鼓励根据上下文推断）。你也可以补充其他你认为重要的软能力。
  例如：{{"沟通能力": {{"score": 4, "description": "需要与产品、开发、测试等多方沟通，协调需求和进度，因此要求较强的沟通协作能力。"}}}}

注意：技能列表应聚焦于本大类核心岗位的常见要求，避免包含明显无关领域的技能（如后端数据库、GIS开发等，除非描述中反复强调）。

岗位描述：
{combined}

只返回JSON，不要其他文字。
"""
    for attempt in range(2):
        result = _call_zhipu(prompt, temperature=0.3, max_tokens=6000)
        if not result:
            continue
        json_match = re.search(r'```json\n(.*?)\n```', result, re.DOTALL)
        if json_match:
            result = json_match.group(1)
        try:
            data = json.loads(result)
            # 处理技能列表：合并去重
            if "skills" in data and isinstance(data["skills"], list):
                data["skills"] = _merge_skills(data["skills"])
            # 处理证书列表：去重
            if "certificates" in data and isinstance(data["certificates"], list):
                data["certificates"] = list(dict.fromkeys(data["certificates"]))
            # 确保 soft_abilities 是字典
            if "soft_abilities" not in data or not isinstance(data["soft_abilities"], dict):
                data["soft_abilities"] = {}
            required = ["创新能力", "学习能力", "抗压能力", "沟通能力", "实习能力"]
            for dim in required:
                if dim not in data["soft_abilities"]:
                    data["soft_abilities"][dim] = {
                        "score": 3,
                        "description": f"根据岗位描述，{dim}是该类岗位常见要求，但未明确提及，给予中等评分。"
                    }
                else:
                    val = data["soft_abilities"][dim]
                    if isinstance(val, (int, float)):
                        data["soft_abilities"][dim] = {
                            "score": int(val),
                            "description": f"{dim}是岗位重要能力。"
                        }
                    elif isinstance(val, dict) and "score" not in val:
                        data["soft_abilities"][dim] = {
                            "score": 3,
                            "description": str(val) if val else f"{dim}是岗位重要能力。"
                        }
            # 保存到数据库
            skills = json.dumps(data.get('skills', []), ensure_ascii=False)
            certificates = json.dumps(data.get('certificates', []), ensure_ascii=False)
            soft_abilities = json.dumps(data.get('soft_abilities', {}), ensure_ascii=False)

            cursor.execute("""
                UPDATE job_categories
                SET skills = ?, certificates = ?, soft_abilities = ?
                WHERE id = ?
            """, (skills, certificates, soft_abilities, category_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"生成大类画像JSON解析失败（尝试 {attempt+1}）：{e}")
    conn.close()
    return False

# ========== 第四步：动态生成长尾岗位画像（优化版） ==========
def generate_dynamic_job_profile(job_name: str) -> Optional[Dict[str, Any]]:
    from db import get_db
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. 检查是否已存在该岗位的单独画像
    cursor.execute("SELECT job_name FROM job_profile WHERE job_name = ?", (job_name,))
    if cursor.fetchone():
        print(f"⚠️ {job_name} 已有单独画像，跳过")
        conn.close()
        return None  # 已存在，不再生成
    
    # 2. 随机抽取10条描述
    cursor.execute(
        "SELECT job_description FROM job WHERE job_name LIKE ? AND job_description IS NOT NULL ORDER BY RANDOM() LIMIT 10",
        (f'%{job_name}%',)
    )
    descs = [row['job_description'] for row in cursor.fetchall() if row['job_description']]
    if not descs:
        print(f"❌ {job_name} 无相关描述，无法生成画像")
        conn.close()
        return None

    # 3. 构造提示词，调用大模型
    combined = "\n---\n".join(descs)
    prompt = f"""
你是一个职业分析师。请根据以下岗位名称和描述，为该岗位生成画像。
岗位名称：{job_name}
描述：
{combined}

要求返回严格的JSON格式，包含：
- skills：必备技能列表，**请合并相似技能**（例如 HTML 和 HTML5 合并为 HTML，Vue 和 Vue3.0 合并为 Vue），并按重要性或出现频率排序。
- certificates：常见证书列表（字符串数组）。
- soft_abilities：软实力要求，对象形式，键为软能力名称，值为包含 `score`（1-5分）和 `description`（详细描述该能力在岗位中的具体体现）的对象。
  请根据描述提炼出最相关的软能力，至少应包含创新能力、学习能力、抗压能力、沟通能力、实习能力（如果这些能力在描述中有体现，请给出评分和描述；如果某个能力完全未提及，可给出默认值，但鼓励根据上下文推断）。你也可以补充其他你认为重要的软能力。
  例如：{{"沟通能力": {{"score": 4, "description": "需要与产品、开发、测试等多方沟通，协调需求和进度，因此要求较强的沟通协作能力。"}}}}

只返回JSON，不要其他文字。
"""
    for attempt in range(2):
        result = _call_zhipu(prompt, temperature=0.3, max_tokens=6000)
        if not result:
            continue
        json_match = re.search(r'```json\n(.*?)\n```', result, re.DOTALL)
        if json_match:
            result = json_match.group(1)
        try:
            data = json.loads(result)
            # 处理技能列表：合并去重
            if "skills" in data and isinstance(data["skills"], list):
                data["skills"] = _merge_skills(data["skills"])
            # 处理证书列表：去重
            if "certificates" in data and isinstance(data["certificates"], list):
                data["certificates"] = list(dict.fromkeys(data["certificates"]))
            # 确保 soft_abilities 是字典
            if "soft_abilities" not in data or not isinstance(data["soft_abilities"], dict):
                data["soft_abilities"] = {}
            required = ["创新能力", "学习能力", "抗压能力", "沟通能力", "实习能力"]
            for dim in required:
                if dim not in data["soft_abilities"]:
                    data["soft_abilities"][dim] = {
                        "score": 3,
                        "description": f"根据岗位描述，{dim}是该岗位常见要求，但未明确提及，给予中等评分。"
                    }
                else:
                    val = data["soft_abilities"][dim]
                    if isinstance(val, (int, float)):
                        data["soft_abilities"][dim] = {
                            "score": int(val),
                            "description": f"{dim}是岗位重要能力。"
                        }
                    elif isinstance(val, dict) and "score" not in val:
                        data["soft_abilities"][dim] = {
                            "score": 3,
                            "description": str(val) if val else f"{dim}是岗位重要能力。"
                        }
            # ========== 插入数据库 ==========
            cursor.execute('''
                INSERT INTO job_profile (job_name, skills, certificates, soft_abilities)
                VALUES (?, ?, ?, ?)
            ''', (
                job_name,
                json.dumps(data.get('skills', []), ensure_ascii=False),
                json.dumps(data.get('certificates', []), ensure_ascii=False),
                json.dumps(data.get('soft_abilities', {}), ensure_ascii=False)
            ))
            conn.commit()
            print(f"✅ {job_name} 画像已存入数据库")
            conn.close()
            return data
        except Exception as e:
            print(f"动态画像生成JSON解析失败（尝试 {attempt+1}）：{e}")
    conn.close()
    return None

# ========== 岗位图谱构建模块 ==========
import json
import re
from collections import defaultdict
from typing import List, Tuple, Dict, Any, Optional

from db import get_db

# -------------------- 辅助函数（从画像中获取各类信息） --------------------
def get_job_description(job_name: str) -> str:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT job_description FROM job WHERE job_name = ? LIMIT 1", (job_name,))
    row = cursor.fetchone()
    conn.close()
    return row['job_description'].strip() if row and row['job_description'] else ""

def get_job_skills(job_name: str) -> List[str]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT skills FROM job_profile WHERE job_name = ?", (job_name,))
    row = cursor.fetchone()
    conn.close()
    if row and row['skills']:
        try:
            return json.loads(row['skills'])
        except:
            return []
    return []

def get_job_certificates(job_name: str) -> List[str]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT certificates FROM job_profile WHERE job_name = ?", (job_name,))
    row = cursor.fetchone()
    conn.close()
    if row and row['certificates']:
        try:
            return json.loads(row['certificates'])
        except:
            return []
    return []

def get_job_soft_abilities(job_name: str) -> Dict[str, Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT soft_abilities FROM job_profile WHERE job_name = ?", (job_name,))
    row = cursor.fetchone()
    conn.close()
    if row and row['soft_abilities']:
        try:
            return json.loads(row['soft_abilities'])
        except:
            return {}
    return {}

def get_job_category(job_name: str) -> str:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.name FROM job_categories c
        JOIN job j ON j.category_id = c.id
        WHERE j.job_name = ?
    """, (job_name,))
    row = cursor.fetchone()
    conn.close()
    return row['name'] if row else ""

def get_all_job_names() -> List[str]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT job_name FROM job")
    rows = cursor.fetchall()
    conn.close()
    return [row['job_name'] for row in rows]

def get_jobs_with_profile() -> List[str]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT job_name FROM job_profile")
    rows = cursor.fetchall()
    conn.close()
    return [row['job_name'] for row in rows]

# -------------------- 级别关键词处理（用于规则兜底） --------------------
LEVEL_KEYWORDS = {
    "实习": 0,
    "初级": 1,
    "中级": 2,
    "高级": 3,
    "资深": 4,
    "专家": 5,
    "架构师": 6,
    "经理": 7,
    "总监": 8,
    "首席": 9,
}

def extract_level(job_title: str) -> int:
    title_lower = job_title.lower()
    max_level = 0
    for kw, level in LEVEL_KEYWORDS.items():
        if kw in title_lower:
            if level > max_level:
                max_level = level
    return max_level

def extract_base_job(job_title: str) -> str:
    base = job_title
    for kw in LEVEL_KEYWORDS.keys():
        base = base.replace(kw, "").strip()
    base = re.sub(r'\s+', ' ', base).strip()
    return base

# -------------------- 相似度计算 --------------------
def get_skill_similarity(job1: str, job2: str) -> float:
    skills1 = set(get_job_skills(job1))
    skills2 = set(get_job_skills(job2))
    if not skills1 or not skills2:
        return 0.0
    intersection = skills1 & skills2
    union = skills1 | skills2
    return len(intersection) / len(union)

def get_soft_ability_similarity(job1: str, job2: str) -> float:
    soft1 = get_job_soft_abilities(job1)
    soft2 = get_job_soft_abilities(job2)
    if not soft1 or not soft2:
        return 0.0
    all_dims = set(soft1.keys()) | set(soft2.keys())
    if not all_dims:
        return 0.0
    v1 = [soft1.get(dim, {}).get('score', 0) for dim in all_dims]
    v2 = [soft2.get(dim, {}).get('score', 0) for dim in all_dims]
    dot = sum(a*b for a,b in zip(v1, v2))
    norm1 = sum(a*a for a in v1)**0.5
    norm2 = sum(b*b for b in v2)**0.5
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

def get_certificate_similarity(job1: str, job2: str) -> float:
    certs1 = set(get_job_certificates(job1))
    certs2 = set(get_job_certificates(job2))
    if not certs1 or not certs2:
        return 0.0
    intersection = certs1 & certs2
    union = certs1 | certs2
    return len(intersection) / len(union)

def get_comprehensive_similarity(job1: str, job2: str, weights=(0.6, 0.3, 0.1)) -> float:
    skill_sim = get_skill_similarity(job1, job2)
    soft_sim = get_soft_ability_similarity(job1, job2)
    cert_sim = get_certificate_similarity(job1, job2)
    return weights[0]*skill_sim + weights[1]*soft_sim + weights[2]*cert_sim

# -------------------- 垂直路径生成 --------------------
def build_vertical_paths() -> List[Tuple[str, str, str, str]]:
    from db import get_db
    conn = get_db()
    cursor = conn.cursor()

    profile_jobs = get_jobs_with_profile()
    if not profile_jobs:
        print("警告：没有有画像的岗位，无法生成垂直路径")
        return []

    # 固定取 18 个岗位
    cursor.execute("""
        SELECT job_name, COUNT(*) as cnt FROM job 
        WHERE job_name IN ({}) 
        GROUP BY job_name 
        ORDER BY cnt DESC 
        LIMIT 18
    """.format(','.join(['?']*len(profile_jobs))), profile_jobs)
    
    core_jobs = [row['job_name'] for row in cursor.fetchall()]
    conn.close()

    relations = []

    for job in core_jobs:
        prompt = f"""
        你是职业规划专家。请根据行业常识，为【{job}】生成标准晋升路径。
        要求：
        1. 只输出连续的上级岗位名称，最多3个；
        2. 必须是真实存在、同领域岗位；
        3. 只返回干净JSON数组，不要任何多余文字、解释、标点。
        示例：["高级工程师","技术主管","技术经理"]
        """
        result = _call_zhipu(prompt, temperature=0.3, max_tokens=6000)
        if not result:
            continue

        try:
            json_match = re.search(r'```json\n(.*?)\n```', result, re.DOTALL)
            if json_match:
                result = json_match.group(1)
            targets = json.loads(result)
            if isinstance(targets, list) and targets:
                prev = job
                for target in targets:
                    from_skills = get_job_skills(prev)
                    from_certs = get_job_certificates(prev)
                    desc_parts = [f"【{prev}】"]

                    if from_skills:
                        skills_desc = "、".join(from_skills[:5])
                        if len(from_skills) > 5:
                            skills_desc += "等"
                        desc_parts.append(f"所需技能：{skills_desc}")

                    if from_certs:
                        certs_desc = "、".join(from_certs[:3])
                        if len(from_certs) > 3:
                            certs_desc += "等"
                        desc_parts.append(f"所需证书：{certs_desc}")

                    desc_parts.append(f"可晋升至【{target}】,需提升技能和管理能力")
                    desc = " ".join(desc_parts)
                    relations.append((prev, target, 'promotion', desc))
                    prev = target
        except Exception as e:
            print(f"晋升路径解析失败 {job}: {e}")

    return relations


# -------------------- 横向路径生成（大类内匹配 + 画像兜底） --------------------
def build_lateral_paths(
    source_jobs: List[str] = None,
    min_paths: int = 3,
    similarity_threshold: float = 0.2  # 温和阈值，保证有结果
) -> List[Tuple[str, str, str, str]]:
    """
    横向路径生成逻辑：
    1. 只在同一大类内匹配岗位
    2. 优先使用岗位独立画像，无独立画像则用大类通用画像
    3. 按技能+软能力+证书相似度排序，取TOP3
    """
    if source_jobs is None:
        source_jobs = get_jobs_with_profile()
    target_jobs = get_all_job_names()

    # 辅助函数：获取岗位/大类画像（兜底逻辑）
    def _get_profile_data(job_name: str, data_type: str) -> Any:
        """
        data_type: skills/certificates/soft_abilities
        优先取岗位独立画像，无则取所属大类画像
        """
        # 1. 尝试取独立画像
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(f"SELECT {data_type} FROM job_profile WHERE job_name = ?", (job_name,))
        row = cursor.fetchone()
        if row and row[data_type]:
            conn.close()
            try:
                return json.loads(row[data_type])
            except:
                pass
        
        # 2. 取所属大类画像兜底
        cursor.execute("""
            SELECT c.{0} FROM job_categories c
            JOIN job j ON j.category_id = c.id
            WHERE j.job_name = ? LIMIT 1
        """.format(data_type), (job_name,))
        row = cursor.fetchone()
        conn.close()
        if row and row[data_type]:
            try:
                return json.loads(row[data_type])
            except:
                pass
        
        # 3. 兜底空值
        if data_type == "soft_abilities":
            return {}
        return []

    # 重写相似度计算（兼容画像兜底）
    def _calc_similarity(job1: str, job2: str) -> float:
        # 技能相似度
        skills1 = set(_get_profile_data(job1, "skills"))
        skills2 = set(_get_profile_data(job2, "skills"))
        skill_sim = len(skills1 & skills2) / len(skills1 | skills2) if (skills1 or skills2) else 0.0
        
        # 软能力相似度（余弦相似度）
        soft1 = _get_profile_data(job1, "soft_abilities")
        soft2 = _get_profile_data(job2, "soft_abilities")
        all_dims = set(soft1.keys()) | set(soft2.keys())
        v1 = [soft1.get(dim, {}).get("score", 0) for dim in all_dims]
        v2 = [soft2.get(dim, {}).get("score", 0) for dim in all_dims]
        dot = sum(a*b for a,b in zip(v1, v2))
        norm1 = sum(a*a for a in v1)**0.5
        norm2 = sum(b*b for b in v2)**0.5
        soft_sim = dot / (norm1 * norm2) if (norm1 and norm2) else 0.0
        
        # 证书相似度
        certs1 = set(_get_profile_data(job1, "certificates"))
        certs2 = set(_get_profile_data(job2, "certificates"))
        cert_sim = len(certs1 & certs2) / len(certs1 | certs2) if (certs1 or certs2) else 0.0
        
        # 权重分配（技能为主，软能力为辅，证书补充）
        return 0.6 * skill_sim + 0.3 * soft_sim + 0.1 * cert_sim

    relations = []
    for job in source_jobs:
        similarities = []
        job_category = get_job_category(job)  # 获取当前岗位大类
        
        # 遍历所有目标岗位，只匹配同大类
        for other in target_jobs:
            if other == job:
                continue
            other_category = get_job_category(other)
            # 只在同一大类内匹配
            if job_category and other_category and job_category != other_category:
                continue
            
            # 计算相似度（兼容画像兜底）
            sim = _calc_similarity(job, other)
            if sim >= similarity_threshold:
                similarities.append((other, sim))
        
        # 按相似度排序，取TOP3
        similarities.sort(key=lambda x: x[1], reverse=True)
        selected = similarities[:min_paths]
        
        # 生成横向路径描述
        for to_job, sim in selected:
            # 获取技能/软能力/证书（兜底逻辑）
            from_skills = set(_get_profile_data(job, "skills"))
            to_skills = set(_get_profile_data(to_job, "skills"))
            from_soft = _get_profile_data(job, "soft_abilities")
            to_soft = _get_profile_data(to_job, "soft_abilities")
            from_certs = set(_get_profile_data(job, "certificates"))
            to_certs = set(_get_profile_data(to_job, "certificates"))
            
            # 计算需补充的能力
            need_skills = to_skills - from_skills
            need_soft = []
            for dim, val in to_soft.items():
                from_score = from_soft.get(dim, {}).get('score', 0)
                to_score = val.get('score', 0)
                if to_score > from_score + 1:
                    need_soft.append(dim)
            need_certs = to_certs - from_certs
            
            # 拼接描述
            desc_parts = [f"【{job}】可换岗至【{to_job}】"]
            if need_skills:
                desc_parts.append(f"需补充技能：{'、'.join(list(need_skills)[:5])}")
            if need_soft:
                desc_parts.append(f"需提升软能力：{'、'.join(need_soft[:3])}")
            if need_certs:
                desc_parts.append(f"建议证书：{'、'.join(list(need_certs)[:3])}")
            
            desc = "；".join(desc_parts)
            relations.append((job, to_job, 'transition', desc))

    return relations

# -------------------- 重建图谱：固定 18 个岗位 --------------------
def rebuild_job_graph() -> Tuple[int, int]:
    from db import get_db
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM job_relations")

    # 生成垂直路径（18个岗位）
    vertical = build_vertical_paths()
    for rel in vertical:
        cursor.execute("INSERT INTO job_relations (from_job, to_job, relation_type, description) VALUES (?, ?, ?, ?)", rel)

    # 横向也用 18 个岗位，每个 3 条路径
    profile_jobs = get_jobs_with_profile()
    source_jobs = profile_jobs[:18] 

    lateral = build_lateral_paths(source_jobs=source_jobs, min_paths=3, similarity_threshold=0.2)

    if lateral:
        for rel in lateral:
            cursor.execute("INSERT INTO job_relations (from_job, to_job, relation_type, description) VALUES (?, ?, ?, ?)", rel)

    conn.commit()
    conn.close()
    print(f"图谱构建完成：18个岗位，垂直路径 {len(vertical)} 条，横向路径 {len(lateral)} 条")
    return len(vertical), len(lateral)