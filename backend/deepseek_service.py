"""
DeepSeek AI 服务模块
支持真实API调用和本地模板降级
"""
import os
import json
import requests
from typing import Optional, Generator

# DeepSeek API配置
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

# 是否启用真实API（需要配置API_KEY）
ENABLE_REAL_API = bool(DEEPSEEK_API_KEY)


def get_system_prompt():
    """获取系统提示词"""
    return """你是华中科技大学的专业学科导师。对于学生的问题，你需要提供深入、准确、完整的解答。

解答要求：
1. **深度分析**：不仅给出答案，更要解释为什么这样做，背后的原理是什么
2. **完整步骤**：每一步都要详细说明，不能跳步骤，列出所有中间计算过程
3. **公式推导**：使用LaTeX格式（行内$...$，块级$$...$$），展示完整的数学推导
4. **概念阐述**：解释涉及的定理、公式、概念，说明适用条件和注意事项
5. **多角度思考**：如果有多种解法，都要提及并比较优劣
6. **易错点提醒**：指出常见错误和需要注意的地方
7. **知识拓展**：关联相关知识点，帮助建立知识体系

格式规范：
- 使用Markdown标题（##）组织内容结构
- 数学公式统一用LaTeX：行内公式$x^2$，块级公式$$\int_0^1 x dx$$
- 重要结论用**加粗**标注
- 最后用$\boxed{}$框出最终答案

禁止：
- 不要过于简略，不要只给结果不给过程
- 不要使用"显然"、"容易得到"等跳步的表述
- 不要忽略单位和符号说明"""


def call_deepseek_api(question: str, subject: str = "数学", stream: bool = False) -> str:
    """
    调用DeepSeek API获取答案
    
    Args:
        question: 题目内容
        subject: 学科类型
        stream: 是否使用流式输出
    
    Returns:
        AI生成的答案
    """
    if not ENABLE_REAL_API:
        return generate_local_answer(question, subject)
    
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        user_prompt = f"请解答以下{subject}题目：\n\n{question}"
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": get_system_prompt()},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 8000,
            "stream": stream
        }
        
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            return format_ai_answer(answer, "DeepSeek")
        else:
            print(f"[DeepSeek API Error] Status: {response.status_code}")
            return generate_local_answer(question, subject)
            
    except requests.exceptions.Timeout:
        print("[DeepSeek API] Request timeout, using local template")
        return generate_local_answer(question, subject)
    except Exception as e:
        print(f"[DeepSeek API Error] {e}")
        return generate_local_answer(question, subject)


def call_deepseek_stream(question: str, subject: str = "数学") -> Generator[str, None, None]:
    """
    流式调用DeepSeek API
    
    Yields:
        逐段返回的答案内容
    """
    if not ENABLE_REAL_API:
        # 模拟流式输出
        answer = generate_local_answer(question, subject)
        for char in answer:
            yield char
        return
    
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        user_prompt = f"请解答以下{subject}题目：\n\n{question}"
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": get_system_prompt()},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 8000,
            "stream": True
        }
        
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=data,
            timeout=90,
            stream=True
        )
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data_str)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
        else:
            # 降级到本地模板
            answer = generate_local_answer(question, subject)
            for char in answer:
                yield char
                
    except Exception as e:
        print(f"[DeepSeek Stream Error] {e}")
        answer = generate_local_answer(question, subject)
        for char in answer:
            yield char


def format_ai_answer(answer: str, model_name: str) -> str:
    """格式化AI答案"""
    return f"""## 🤖 {model_name} AI 实时解答

{answer}

---
*🤖 由 {model_name} AI 实时生成 | 仅供学习参考*
"""


def generate_local_answer(question: str, subject: str) -> str:
    """
    生成本地模板答案（当API不可用时使用）
    """
    # 分析题目类型
    question_analysis = analyze_question(question)
    
    return f"""## 🤖 AI 智能解答

**📋 题目内容**：
> {question if len(question) < 300 else question[:300] + '...'}

### 📚 学科分类：{subject}
### 🎯 题型识别：{question_analysis['type']}

---

### 📝 解题思路

**第一步：理解题意**
{question_analysis['understanding']}

**第二步：选择方法**
{question_analysis['method']}

**第三步：具体求解**
{question_analysis['solution']}

**第四步：验证答案**
- 检查计算过程是否有误
- 验证答案是否符合题目要求
- 考虑是否有特殊情况

---

### 📖 相关知识点

{question_analysis['knowledge']}

### 💡 学习建议

1. 理解核心概念和定义
2. 熟记重要公式及其适用条件
3. 多做同类型练习题
4. 总结解题技巧和易错点

---
⚠️ **提示**：本答案由AI模板生成，建议参考教材和标准答案进行学习。

*🤖 AI 辅助生成 | 仅供学习参考*
"""


def analyze_question(question: str) -> dict:
    """分析题目类型和生成解答模板"""
    result = {
        'type': '综合题',
        'understanding': '仔细阅读题目，明确已知条件和求解目标。',
        'method': '根据题目特点选择合适的解题方法。',
        'solution': '按照选定的方法逐步求解。',
        'knowledge': '- 基本概念和定义\n- 核心公式和定理\n- 解题技巧和方法'
    }
    
    # 证明题
    if '证明' in question or '证' in question:
        result['type'] = '证明题'
        result['understanding'] = '明确要证明的结论，分析可用的条件。'
        result['method'] = '可以尝试直接证明、反证法、数学归纳法等方法。'
        result['solution'] = '从已知条件出发，通过逻辑推理逐步推导出结论。'
        result['knowledge'] = '- 证明方法：直接法、反证法、归纳法\n- 逻辑推理规则\n- 常用不等式和恒等式'
    
    # 计算题
    elif '求' in question or '计算' in question:
        result['type'] = '计算题'
        result['understanding'] = '识别计算对象，确定计算公式。'
        result['method'] = '套用相关公式，注意计算技巧。'
        result['solution'] = '代入数值，分步计算，化简结果。'
        result['knowledge'] = '- 计算公式和法则\n- 简化计算的技巧\n- 结果的表示形式'
    
    # 积分题
    if '积分' in question or '∫' in question:
        result['type'] = '积分计算题'
        result['method'] = '判断积分类型，选择换元法、分部积分法或其他技巧。'
        result['knowledge'] = '- 基本积分公式\n- 换元积分法\n- 分部积分法\n- 有理函数积分'
    
    # 极限题
    elif '极限' in question or 'lim' in question.lower():
        result['type'] = '极限计算题'
        result['method'] = '判断极限类型，使用等价无穷小、洛必达法则或泰勒展开。'
        result['knowledge'] = '- 重要极限公式\n- 等价无穷小替换\n- 洛必达法则\n- 泰勒级数展开'
    
    # 矩阵题
    elif '矩阵' in question or '特征值' in question:
        result['type'] = '线性代数题'
        result['method'] = '利用矩阵运算法则，求解特征值、特征向量或进行矩阵分解。'
        result['knowledge'] = '- 矩阵基本运算\n- 行列式计算\n- 特征值与特征向量\n- 矩阵对角化'
    
    # 电路题
    elif '电路' in question or '电阻' in question or '电压' in question:
        result['type'] = '电路分析题'
        result['method'] = '运用基尔霍夫定律、欧姆定律等基本电路定律。'
        result['knowledge'] = '- 基尔霍夫定律\n- 欧姆定律\n- 电路等效变换\n- 功率计算'
    
    return result


def check_api_status() -> dict:
    """检查API状态"""
    return {
        'api_enabled': ENABLE_REAL_API,
        'api_key_configured': bool(DEEPSEEK_API_KEY),
        'api_url': DEEPSEEK_API_URL,
        'fallback_mode': not ENABLE_REAL_API
    }


# 测试代码
if __name__ == '__main__':
    print("DeepSeek API Status:", check_api_status())
    
    test_question = "求函数 f(x) = x² + 2x + 1 的最小值"
    print("\n测试题目:", test_question)
    print("\n" + "=" * 50)
    
    answer = call_deepseek_api(test_question, "高等数学")
    print(answer)
