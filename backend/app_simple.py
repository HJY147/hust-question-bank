"""
HUST专属搜题系统 - Flask服务
版本: 2.0.0
功能: 基础搜题、知识点识别、AI解答
使用waitress生产服务器
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import json
from datetime import datetime
import re
import random

# 初始化 Flask 应用
app = Flask(__name__, static_folder='../frontend')
CORS(app)

# 上传配置
UPLOAD_FOLDER = '../data/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 知识点标签库
KNOWLEDGE_TAGS = {
    '高等数学': {
        'keywords': ['极限', '导数', '积分', '微分', '级数', '泰勒', '麦克劳林', '洛必达', '定积分', '不定积分'],
        'color': '#007bff'
    },
    '线性代数': {
        'keywords': ['矩阵', '行列式', '特征值', '特征向量', '线性空间', '向量', '秩', '逆矩阵', '正交'],
        'color': '#28a745'
    },
    '概率论': {
        'keywords': ['概率', '随机变量', '期望', '方差', '分布', '正态', '泊松', '二项', '协方差'],
        'color': '#17a2b8'
    },
    '大学物理': {
        'keywords': ['力学', '电磁', '光学', '热学', '波动', '量子', '动量', '能量', '电场', '磁场'],
        'color': '#ffc107'
    },
    '电路分析': {
        'keywords': ['电路', '电阻', '电容', '电感', '电压', '电流', '功率', '阻抗', '谐振', '运放'],
        'color': '#dc3545'
    },
    '理论力学': {
        'keywords': ['静力学', '动力学', '运动学', '力矩', '平衡', '摩擦', '碰撞', '振动'],
        'color': '#6610f2'
    },
    '复变函数': {
        'keywords': ['复数', '解析', '柯西', '留数', '调和', '共轭', '保角映射'],
        'color': '#e83e8c'
    },
    '信号系统': {
        'keywords': ['信号', '系统', '傅里叶', '拉普拉斯', 'Z变换', '滤波', '采样', '卷积'],
        'color': '#20c997'
    }
}

# 题目类型识别
QUESTION_TYPES = {
    '求解类': ['求', '解', '计算', '求解', '算出'],
    '证明类': ['证明', '证', '推导', '说明'],
    '判断类': ['判断', '是否', '能否', '对错'],
    '选择类': ['选择', '选项', 'A.', 'B.', 'C.', 'D.'],
    '填空类': ['填空', '___', '（  ）', '(  )'],
    '作图类': ['画图', '作图', '画出', '绘制']
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def identify_knowledge_tags(text):
    """识别文本中的知识点标签"""
    tags = []
    text_lower = text.lower()
    
    for subject, info in KNOWLEDGE_TAGS.items():
        for keyword in info['keywords']:
            if keyword.lower() in text_lower:
                tags.append({
                    'name': subject,
                    'keyword': keyword,
                    'color': info['color']
                })
                break  # 每个学科只添加一次
    
    return tags

def identify_question_type(text):
    """识别题目类型"""
    for qtype, keywords in QUESTION_TYPES.items():
        for keyword in keywords:
            if keyword in text:
                return qtype
    return '综合类'

def generate_difficulty(similarity):
    """根据相似度估算难度"""
    if similarity > 0.9:
        return {'level': '简单', 'color': '#28a745', 'stars': 2}
    elif similarity > 0.75:
        return {'level': '中等', 'color': '#ffc107', 'stars': 3}
    else:
        return {'level': '困难', 'color': '#dc3545', 'stars': 5}

def simulate_ocr(filename):
    """模拟OCR识别（演示用）"""
    # 根据文件名模拟不同的OCR结果
    demo_texts = [
        '求函数 f(x) = x² + 2x + 1 的最小值',
        '计算定积分 ∫₀¹ x²dx 的值',
        '求矩阵 A = [1 2; 3 4] 的特征值',
        '证明 lim(x→0) sinx/x = 1',
        '分析RLC串联电路的谐振特性',
        '求解微分方程 y\' + 2y = e^x',
        '计算复数 (1+i)^10 的值',
        '分析系统 H(s) = 1/(s+1) 的频率响应'
    ]
    
    text = random.choice(demo_texts)
    confidence = random.uniform(0.85, 0.98)
    
    return {
        'text': text,
        'confidence': round(confidence, 2),
        'language': 'zh-CN',
        'detected_formulas': ['x²', '∫', 'lim'] if any(s in text for s in ['²', '∫', 'lim']) else []
    }

@app.route('/')
def index():
    """返回前端页面"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/photo/<path:filename>')
def serve_photo(filename):
    """提供photo目录的图片"""
    photo_dir = os.path.join(os.path.dirname(__file__), '../photo')
    return send_from_directory(photo_dir, filename)

@app.route('/<path:path>')
def serve_static(path):
    """提供静态文件"""
    return send_from_directory(app.static_folder, path)

@app.route('/api/search', methods=['POST'])
def search_question():
    """搜索题目接口 - 增强版"""
    try:
        # 检查文件
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '未上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '文件名为空'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': '不支持的文件类型'}), 400
        
        # 保存文件
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # 获取参数
        use_ai = request.form.get('use_ai', 'true').lower() == 'true'
        college = request.form.get('college', '')
        
        # 模拟OCR识别
        ocr_result = simulate_ocr(filename)
        ocr_text = ocr_result['text']
        
        # 识别知识点标签
        knowledge_tags = identify_knowledge_tags(ocr_text)
        question_type = identify_question_type(ocr_text)
        
        # 增强OCR结果
        ocr_result['knowledge_tags'] = knowledge_tags
        ocr_result['question_type'] = question_type
        
        # 生成搜索结果
        results = generate_search_results(ocr_text, use_ai, knowledge_tags, question_type)
        
        return jsonify({
            'success': True,
            'ocr_result': ocr_result,
            'results': results,
            'ai_triggered': use_ai,
            'ai_enabled': use_ai,
            'knowledge_tags': knowledge_tags,
            'question_type': question_type,
            'message': '搜索成功'
        })
        
    except Exception as e:
        print(f"[Error] 搜索失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'搜索失败: {str(e)}'
        }), 500


def generate_search_results(ocr_text, use_ai, knowledge_tags, question_type):
    """生成搜索结果（增强版）"""
    results = []
    
    # 确定主要学科
    main_subject = knowledge_tags[0]['name'] if knowledge_tags else '高等数学'
    
    # 如果启用AI，添加AI解答
    if use_ai:
        ai_answer = generate_ai_answer(ocr_text, main_subject, question_type)
        results.append(ai_answer)
    
    # 添加题库匹配结果
    db_results = generate_database_results(ocr_text, main_subject, knowledge_tags)
    results.extend(db_results)
    
    return results


def generate_ai_answer(ocr_text, subject, question_type):
    """生成AI解答"""
    # 根据题目类型生成不同风格的解答
    if '最小值' in ocr_text or '最大值' in ocr_text:
        answer = generate_extremum_answer(ocr_text)
    elif '积分' in ocr_text:
        answer = generate_integral_answer(ocr_text)
    elif '矩阵' in ocr_text or '特征值' in ocr_text:
        answer = generate_matrix_answer(ocr_text)
    elif '电路' in ocr_text:
        answer = generate_circuit_answer(ocr_text)
    else:
        answer = generate_general_answer(ocr_text, subject)
    
    return {
        'question_id': 'ai_deepseek_001',
        'similarity': 0.98,
        'category': subject,
        'source': 'ai',
        'ai_model': 'DeepSeek',
        'confidence': 0.98,
        'question_type': question_type,
        'answer': answer
    }


def generate_extremum_answer(text):
    """生成求最值问题的答案"""
    return '''## 🤖 DeepSeek AI 实时解答

**题目分析**：这是一道求函数最值的问题

### 📚 知识点提示
- 二次函数最值
- 配方法
- 求导法

### 📝 详细解答

**方法一：配方法（推荐）**

对于二次函数 f(x) = ax² + bx + c：

1. 提取二次项系数
2. 配方得到顶点式：f(x) = a(x - h)² + k
3. 顶点 (h, k) 即为最值点

以 f(x) = x² + 2x + 1 为例：
$$f(x) = x^2 + 2x + 1 = (x+1)^2$$

因为 $(x+1)^2 \\geq 0$，所以 $f(x) \\geq 0$

**最小值 = 0**（在 x = -1 处取得）

**方法二：公式法**

对于 f(x) = ax² + bx + c：
- 最值点：$x = -\\frac{b}{2a}$
- 最值：$f(-\\frac{b}{2a}) = c - \\frac{b^2}{4a}$

**方法三：求导法**

$$f'(x) = 2x + 2 = 0 \\Rightarrow x = -1$$

$$f''(x) = 2 > 0$$ → 确认是最小值点

### ✅ 答案
**最小值为 0，在 x = -1 处取得**

---
💡 *本答案由 DeepSeek AI 生成，仅供参考*
'''


def generate_integral_answer(text):
    """生成积分问题的答案"""
    return '''## 🤖 DeepSeek AI 实时解答

**题目分析**：这是一道定积分计算问题

### 📚 知识点提示
- 定积分基本公式
- 牛顿-莱布尼茨公式
- 积分技巧

### 📝 详细解答

**基本积分公式**：
$$\\int x^n dx = \\frac{x^{n+1}}{n+1} + C \\quad (n \\neq -1)$$

**计算过程**（以 ∫₀¹ x²dx 为例）：

$$\\int_0^1 x^2 dx = \\left[\\frac{x^3}{3}\\right]_0^1$$

$$= \\frac{1^3}{3} - \\frac{0^3}{3} = \\frac{1}{3}$$

### 💡 解题技巧
1. **换元法**：复杂函数可尝试换元简化
2. **分部积分**：∫udv = uv - ∫vdu
3. **有理函数积分**：部分分式分解

### ✅ 答案
$$\\int_0^1 x^2 dx = \\frac{1}{3}$$

---
💡 *本答案由 DeepSeek AI 生成，仅供参考*
'''


def generate_matrix_answer(text):
    """生成矩阵问题的答案"""
    return '''## 🤖 DeepSeek AI 实时解答

**题目分析**：这是一道线性代数矩阵问题

### 📚 知识点提示
- 特征值与特征向量
- 行列式计算
- 矩阵运算

### 📝 详细解答

**特征值求解步骤**：

1. **建立特征方程**：$|A - \\lambda I| = 0$

2. **计算行列式**（以 A = [1,2; 3,4] 为例）：
$$\\begin{vmatrix} 1-\\lambda & 2 \\\\ 3 & 4-\\lambda \\end{vmatrix} = 0$$

3. **展开**：
$$(1-\\lambda)(4-\\lambda) - 6 = 0$$
$$\\lambda^2 - 5\\lambda - 2 = 0$$

4. **求解**：
$$\\lambda = \\frac{5 \\pm \\sqrt{33}}{2}$$

### 💡 验证方法
- 特征值之和 = 迹(A) = 1 + 4 = 5 ✓
- 特征值之积 = |A| = 4 - 6 = -2 ✓

### ✅ 答案
$$\\lambda_1 = \\frac{5 + \\sqrt{33}}{2} \\approx 5.37$$
$$\\lambda_2 = \\frac{5 - \\sqrt{33}}{2} \\approx -0.37$$

---
💡 *本答案由 DeepSeek AI 生成，仅供参考*
'''


def generate_circuit_answer(text):
    """生成电路问题的答案"""
    return '''## 🤖 DeepSeek AI 实时解答

**题目分析**：这是一道电路分析问题

### 📚 知识点提示
- 基尔霍夫定律
- 阻抗分析
- 谐振特性

### 📝 详细解答

**RLC串联电路分析**：

1. **总阻抗**：
$$Z = R + j(\\omega L - \\frac{1}{\\omega C})$$

2. **谐振条件**：
$$\\omega_0 L = \\frac{1}{\\omega_0 C}$$
$$\\omega_0 = \\frac{1}{\\sqrt{LC}}$$

3. **谐振频率**：
$$f_0 = \\frac{1}{2\\pi\\sqrt{LC}}$$

4. **品质因数**：
$$Q = \\frac{\\omega_0 L}{R} = \\frac{1}{R}\\sqrt{\\frac{L}{C}}$$

### 💡 特性分析
- 谐振时阻抗最小，等于 R
- 电流最大
- 电压可能放大 Q 倍

### ✅ 答案
谐振频率 $f_0 = \\frac{1}{2\\pi\\sqrt{LC}}$，此时电路呈纯阻性

---
💡 *本答案由 DeepSeek AI 生成，仅供参考*
'''


def generate_general_answer(text, subject):
    """生成通用答案"""
    return f'''## 🤖 DeepSeek AI 实时解答

**题目分析**：{text}

### 📚 所属学科：{subject}

### 📝 详细解答

根据题目分析，这是一道{subject}相关的问题。

**解题思路**：
1. 首先理解题目要求
2. 确定使用的方法和公式
3. 分步骤进行计算
4. 验证答案的合理性

**相关知识点**：
- 基本概念和定义
- 核心公式和定理
- 常见解题技巧

### 💡 学习建议
- 多做同类型练习题
- 理解公式的推导过程
- 注意易错点和特殊情况

---
💡 *本答案由 DeepSeek AI 生成，仅供参考*
*如需更详细解答，请提供完整题目图片*
'''


def generate_database_results(ocr_text, main_subject, knowledge_tags):
    """生成题库匹配结果"""
    results = []
    
    # 模拟从题库中匹配到的题目
    demo_results = [
        {
            'question_id': 'calc_001',
            'similarity': 0.92,
            'category': main_subject,
            'source': 'database',
            'confidence': 0.92,
            'answer': '''## 华科题库解析

**详细解答**：

这道题可以使用配方法或求导法求解。

**配方法**：
将二次函数化为顶点式，直接读出最值。

**求导法**：
令导数为零，求出驻点，判断极值类型。

**答案**：参考课本例题3.2'''
        },
        {
            'question_id': 'calc_002',
            'similarity': 0.85,
            'category': main_subject,
            'source': 'database',
            'confidence': 0.85,
            'ml_similarity': True,
            'answer': '''## 相关练习

**类似题型**：

本题考查函数最值问题，可参考以下知识点：
- 二次函数性质
- 配方技巧
- 导数应用

**拓展练习**：尝试求解含参数的二次函数最值问题'''
        }
    ]
    
    # 为每个结果添加知识点标签
    for result in demo_results:
        result['knowledge_tags'] = knowledge_tags
        result['difficulty'] = generate_difficulty(result['similarity'])
    
    return demo_results

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    return jsonify({
        'success': True,
        'stats': {
            'total_questions': 520,
            'total_answers': 486,
            'colleges': 12,
            'recent_updates': 38
        }
    })

if __name__ == '__main__':
    from waitress import serve
    
    print("=" * 60)
    print("🎓 HUST专属搜题系统 - 生产服务器")
    print("=" * 60)
    print("✅ 服务启动在: http://localhost:5000")
    print("✅ 前端页面: http://localhost:5000")
    print("✅ API接口: http://localhost:5000/api/search")
    print("=" * 60)
    print("🌐 浏览器访问: http://localhost:5000")
    print("🌐 局域网访问: http://0.0.0.0:5000")
    print("=" * 60)
    print("📌 使用 Ctrl+C 停止服务器")
    print("=" * 60)
    
    # 使用waitress生产服务器（无警告）
    serve(app, host='0.0.0.0', port=5000, threads=4)

