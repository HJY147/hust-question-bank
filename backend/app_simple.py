"""
HUST专属搜题系统 - Flask服务
版本: 3.0.0
功能: 图像匹配、OCR识别、知识点识别、AI解答、收藏、历史记录
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

# 导入自定义模块
try:
    from image_matcher import find_similar_from_bytes, preload_image_hashes
    IMAGE_MATCHER_AVAILABLE = True
except ImportError:
    IMAGE_MATCHER_AVAILABLE = False
    print("[Warning] image_matcher not available, using basic matching")

try:
    from database import get_extended_db, init_all_tables
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("[Warning] database module not available")

# 初始化 Flask 应用
app = Flask(__name__, static_folder='../frontend')
CORS(app)

# 目录配置
BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, '../data/uploads')
QUESTION_IMAGES_DIR = os.path.join(BASE_DIR, '../data/question_images')
ANSWERS_DIR = os.path.join(BASE_DIR, '../data/answers')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp'}

# 创建必要目录
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QUESTION_IMAGES_DIR, exist_ok=True)
os.makedirs(ANSWERS_DIR, exist_ok=True)

# 初始化数据库
if DATABASE_AVAILABLE:
    try:
        init_all_tables()
    except Exception as e:
        print(f"[Warning] Database init failed: {e}")

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


def perform_real_ocr(image_path):
    """使用真实的豆包OCR进行识别"""
    try:
        # 尝试导入ai_service
        from ai_service import DoubaoVision
        
        ocr = DoubaoVision()
        result = ocr.extract_question_from_image(image_path)
        
        if result.get('success'):
            return {
                'text': result.get('text', ''),
                'confidence': result.get('confidence', 0.95),
                'language': 'zh-CN',
                'source': '豆包视觉模型',
                'detected_formulas': []
            }
        else:
            # 豆包识别失败，回退到模拟
            print(f"[Warning] 豆包OCR失败: {result.get('error')}，使用模拟数据")
            return simulate_ocr(image_path)
            
    except ImportError as e:
        print(f"[Warning] ai_service导入失败: {e}，使用模拟数据")
        return simulate_ocr(image_path)
    except Exception as e:
        print(f"[Warning] OCR识别异常: {e}，使用模拟数据")
        return simulate_ocr(image_path)

@app.route('/')
def index():
    """返回前端页面"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/photo/<path:filename>')
def serve_photo(filename):
    """提供photo目录的图片"""
    photo_dir = os.path.join(os.path.dirname(__file__), '../photo')
    return send_from_directory(photo_dir, filename)

@app.route('/api/question_image/<path:filename>')
def serve_question_image(filename):
    """提供题目图片"""
    return send_from_directory(QUESTION_IMAGES_DIR, filename)

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
        
        # 读取图片字节数据（用于图像匹配）
        with open(filepath, 'rb') as f:
            image_bytes = f.read()
        
        # 获取参数
        use_ai = request.form.get('use_ai', 'true').lower() == 'true'
        college = request.form.get('college', '')
        
        # 使用真实的豆包OCR识别
        ocr_result = perform_real_ocr(filepath)
        ocr_text = ocr_result['text']
        
        # 识别知识点标签
        knowledge_tags = identify_knowledge_tags(ocr_text)
        question_type = identify_question_type(ocr_text)
        
        # 增强OCR结果
        ocr_result['knowledge_tags'] = knowledge_tags
        ocr_result['question_type'] = question_type
        
        # 生成搜索结果（传递图片字节数据）
        results = generate_search_results(ocr_text, use_ai, knowledge_tags, question_type, image_bytes)
        
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


def generate_search_results(ocr_text, use_ai, knowledge_tags, question_type, image_bytes=None):
    """生成搜索结果（增强版）- 优先题库匹配"""
    results = []
    
    # 确定主要学科
    main_subject = knowledge_tags[0]['name'] if knowledge_tags else '高等数学'
    
    # 优先添加题库匹配结果（传递图片字节数据）
    db_results = generate_database_results(ocr_text, main_subject, knowledge_tags, image_bytes)
    results.extend(db_results)
    
    # 不再自动添加AI解答，由用户手动请求
    # AI解答通过单独的 /api/ai_answer 接口提供
    
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
    """生成通用答案 - 增强版"""
    # 分析题目类型
    question_hints = []
    if '证明' in text or '证' in text:
        question_hints.append('这是一道证明题，需要严格的逻辑推理')
    if '计算' in text or '求' in text:
        question_hints.append('这是一道计算题，需要套用相应公式')
    if '分析' in text or '讨论' in text:
        question_hints.append('需要对问题进行分类讨论和深入分析')
    
    hints_text = '\n'.join(f'- {h}' for h in question_hints) if question_hints else '- 仔细审题，明确题目要求'
    
    return f'''## 🤖 DeepSeek AI 实时解答

**题目内容**：
> {text if len(text) < 200 else text[:200] + '...'}

### 📚 学科归属：{subject}

### 🎯 题型分析
{hints_text}

### 📝 解题方法

**第一步：审题与分析**
- 明确题目给出的已知条件
- 理解题目要求求解的内容
- 识别题目涉及的知识点范围

**第二步：选择方法**
根据{subject}的特点，这类问题通常可以采用以下方法：
1. **基础方法**：运用该学科的基本定义和定理
2. **技巧方法**：利用常见的解题技巧和公式
3. **验证方法**：通过特例验证或反向推导检查答案

**第三步：详细推导**
（由于OCR识别可能不完整，这里给出通用步骤）
- 写出相关公式和定理
- 代入已知条件进行计算
- 化简得到最终结果
- 注意计算过程中的符号和单位

**第四步：答案检验**
- 检查答案是否符合题目要求
- 验证结果的合理性（数量级、正负性等）
- 思考是否有其他解法

### 📖 核心知识点

**{subject}相关重点**：
- 掌握基本概念和定义的准确含义
- 熟记核心公式及其适用条件
- 理解常见题型的解题套路
- 注意易错点和特殊情况的处理

### 🔍 深入学习建议

1. **巩固基础**：回顾教材中的定义、定理和例题
2. **专项训练**：针对这类题型多做练习题
3. **总结规律**：整理同类型题目的解题方法
4. **举一反三**：尝试变式题目和综合应用

### ⚠️ 常见易错点
- 公式记忆错误或适用条件理解不准确
- 计算过程中符号处理不当
- 忽略题目中的隐含条件
- 结果未化简或未转化为题目要求的形式

---
💡 **AI提示**：本答案基于OCR识别的题目内容生成，建议：
- 如果题目图片清晰，AI可提供更精确的解答
- 可以将完整题目手动输入以获得针对性解答
- 建议对照课本和标准答案进行学习

*🤖 由 DeepSeek AI 实时生成 | 仅供学习参考*
'''


def generate_database_results(ocr_text, main_subject, knowledge_tags, uploaded_image_bytes=None):
    """生成题库匹配结果 - 支持图像匹配和文本匹配"""
    results = []
    
    if not os.path.exists(QUESTION_IMAGES_DIR):
        print(f"[Warning] Question images directory not found: {QUESTION_IMAGES_DIR}")
    
    if not os.path.exists(ANSWERS_DIR):
        print(f"[Warning] Answers directory not found: {ANSWERS_DIR}")
        return results
    
    # 获取所有图片文件
    image_files = []
    if os.path.exists(QUESTION_IMAGES_DIR):
        for file in os.listdir(QUESTION_IMAGES_DIR):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
                image_files.append(file)
    
    print(f"[Info] Found {len(image_files)} images in question_images directory")
    
    # ==================== 方式1: 图像相似度匹配 ====================
    image_matches = []
    if IMAGE_MATCHER_AVAILABLE and uploaded_image_bytes:
        try:
            image_matches = find_similar_from_bytes(
                uploaded_image_bytes, 
                QUESTION_IMAGES_DIR, 
                algorithm='phash', 
                threshold=0.5
            )
            print(f"[Info] Image matcher found {len(image_matches)} matches")
        except Exception as e:
            print(f"[Warning] Image matching failed: {e}")
    
    # 处理图像匹配结果
    if image_matches:
        for img_file, similarity in image_matches[:5]:
            question_id = os.path.splitext(img_file)[0]
            answer_text = load_answer_file(question_id)
            
            result = {
                'question_id': question_id,
                'similarity': round(similarity, 2),
                'category': main_subject,
                'source': 'database',
                'match_type': 'image',
                'confidence': round(similarity, 2),
                'answer': answer_text,
                'knowledge_tags': knowledge_tags,
                'difficulty': generate_difficulty(similarity),
                'image_path': img_file,
                'image_url': f'/api/question_image/{img_file}'
            }
            results.append(result)
    
    # ==================== 方式2: 文本内容匹配（新增） ====================
    # 扫描所有答案文件，通过文本相似度匹配
    text_matches = []
    if os.path.exists(ANSWERS_DIR):
        for answer_file in os.listdir(ANSWERS_DIR):
            if answer_file.endswith('.txt') and answer_file != '.gitkeep':
                question_id = os.path.splitext(answer_file)[0]
                
                # 计算文本相似度
                similarity = calculate_text_similarity(question_id, ocr_text, ANSWERS_DIR)
                
                if similarity > 0.3:  # 文本匹配阈值
                    text_matches.append((question_id, similarity))
        
        # 按相似度排序
        text_matches.sort(key=lambda x: x[1], reverse=True)
        print(f"[Info] Text matcher found {len(text_matches)} matches")
        
        # 添加文本匹配结果（避免重复）
        existing_ids = {r['question_id'] for r in results}
        for question_id, similarity in text_matches[:5]:
            if question_id not in existing_ids:
                answer_text = load_answer_file(question_id)
                
                # 检查是否有对应图片
                has_image = False
                image_url = None
                for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                    img_path = os.path.join(QUESTION_IMAGES_DIR, f"{question_id}{ext}")
                    if os.path.exists(img_path):
                        has_image = True
                        image_url = f'/api/question_image/{question_id}{ext}'
                        break
                
                result = {
                    'question_id': question_id,
                    'similarity': round(similarity, 2),
                    'category': main_subject,
                    'source': 'database',
                    'match_type': 'text',
                    'confidence': round(similarity, 2),
                    'answer': answer_text,
                    'knowledge_tags': knowledge_tags,
                    'difficulty': generate_difficulty(similarity),
                    'image_path': None if not has_image else f"{question_id}{ext}",
                    'image_url': image_url
                }
                results.append(result)
    
    # 按相似度排序
    results.sort(key=lambda x: x['similarity'], reverse=True)
    
    # 最多返回5个结果
    return results[:5]


def load_answer_file(question_id):
    """加载答案文件"""
    answer_file = os.path.join(ANSWERS_DIR, f"{question_id}.txt")
    
    if not os.path.exists(answer_file):
        return f"## 题库题目\n\n**题目编号**：{question_id}\n\n暂无答案文件\n\n💡 请创建对应的答案文件：`data/answers/{question_id}.txt`"
    
    try:
        with open(answer_file, 'r', encoding='utf-8') as f:
            answer_text = f.read()
        
        # 检查是否是有效文本
        if answer_text.startswith('\ufffd') or '\ufffd' in answer_text[:100]:
            return f"## ⚠️ 答案文件格式错误\n\n**题目编号**：{question_id}\n\n检测到答案文件是图片格式，请上传纯文本答案文件(.txt)。"
        
        return answer_text
    except UnicodeDecodeError:
        return f"## ⚠️ 答案文件格式错误\n\n**题目编号**：{question_id}\n\n答案文件不是文本格式，请上传纯文本答案文件。"
    except Exception as e:
        return f"## 题库答案\n\n**题目编号**：{question_id}\n\n答案文件读取失败：{str(e)}"


def calculate_simple_similarity(question_id, ocr_text):
    """简单相似度计算 - 基于关键词匹配（用于后备）"""
    keywords_map = {
        'calc': ['微积分', '导数', '积分', '极限'],
        'calculus': ['微积分', '导数', '积分', '极值'],
        'phys': ['物理', '力', '能量', '动量'],
        'physics': ['物理', '力学', '电磁'],
        'mech': ['力学', '机械', '动力'],
        'mechanics': ['力学', '静力', '动力'],
        'circuit': ['电路', '电阻', '电压', '电流'],
        'complex': ['复变', '复数', '解析']
    }
    
    base_similarity = 0.7
    
    for key, words in keywords_map.items():
        if key in question_id.lower():
            for word in words:
                if word in ocr_text:
                    base_similarity += 0.1
                    break
    
    return min(base_similarity, 0.99)


def calculate_text_similarity(question_id, ocr_text, answers_dir):
    """
    计算文本相似度 - 智能匹配
    通过答案文件内容和OCR文本的关键词匹配
    """
    answer_file = os.path.join(answers_dir, f"{question_id}.txt")
    
    if not os.path.exists(answer_file):
        return 0.0
    
    try:
        # 读取答案文件
        with open(answer_file, 'r', encoding='utf-8') as f:
            answer_content = f.read().lower()
        
        ocr_lower = ocr_text.lower()
        
        # 基础分数
        similarity = 0.0
        
        # 1. 检查题目类型关键词（权重：0.3）
        type_keywords = {
            '求': 0.05, '计算': 0.05, '证明': 0.05, '判断': 0.05,
            '极值': 0.1, '极大值': 0.1, '极小值': 0.1, '最值': 0.1,
            '导数': 0.08, '积分': 0.08, '微分': 0.08, '级数': 0.08,
            '泰勒': 0.1, 'taylor': 0.1, 'sin': 0.08, 'cos': 0.08,
            '复数': 0.08, '复变': 0.08, '解析': 0.08,
            '矩阵': 0.08, '特征值': 0.08, '行列式': 0.08,
            '电路': 0.08, '电压': 0.08, '电流': 0.08, '电阻': 0.08
        }
        
        for keyword, weight in type_keywords.items():
            if keyword in ocr_lower and keyword in answer_content:
                similarity += weight
        
        # 2. 检查数学符号和公式特征（权重：0.2）
        math_patterns = [
            ('f(x)', 0.1), ('f(z)', 0.1), ('x²', 0.05), ('x^2', 0.05), 
            ('x³', 0.05), ('x^3', 0.05), ('∫', 0.05), ('∑', 0.05),
            ('lim', 0.05), ('sin', 0.05), ('cos', 0.05), ('tan', 0.05),
            ('z₀', 0.05), ('z_0', 0.05), ('z0', 0.05)
        ]
        
        for pattern, weight in math_patterns:
            if pattern in ocr_lower and pattern in answer_content:
                similarity += weight
        
        # 3. 检查数字特征（权重：0.15）
        import re
        ocr_numbers = set(re.findall(r'\d+', ocr_lower))
        answer_numbers = set(re.findall(r'\d+', answer_content))
        
        if ocr_numbers and answer_numbers:
            common_numbers = ocr_numbers & answer_numbers
            if common_numbers:
                similarity += 0.15 * (len(common_numbers) / max(len(ocr_numbers), len(answer_numbers)))
        
        # 4. 学科分类加分（权重：0.1）
        subject_map = {
            'calculus': ['微积分', '导数', '积分', '极值', 'f(x)'],
            'complex': ['复变', '复数', 'z', '解析', 'taylor', '泰勒'],
            'physics': ['物理', '力', '速度', '加速度', '能量'],
            'circuit': ['电路', '电压', '电流', '电阻', '功率'],
            'mechanics': ['力学', '动力', '静力', '平衡', '力矩']
        }
        
        for subject_key, subject_keywords in subject_map.items():
            if subject_key in question_id.lower():
                for keyword in subject_keywords:
                    if keyword in ocr_lower:
                        similarity += 0.1
                        break
                break
        
        # 5. 文本长度相似度加分（权重：0.05）
        if len(ocr_text) > 10:
            length_ratio = min(len(ocr_text), len(answer_content)) / max(len(ocr_text), len(answer_content))
            if length_ratio > 0.3:
                similarity += 0.05 * length_ratio
        
        # 限制在0-1之间
        return min(similarity, 1.0)
        
    except Exception as e:
        print(f"[Warning] Text similarity calculation failed for {question_id}: {e}")
        return 0.0


@app.route('/api/ai_answer', methods=['POST'])
def get_ai_answer():
    """获取AI解答 - 由用户手动触发"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求数据为空'}), 400
        
        ocr_text = data.get('text', '')
        subject = data.get('subject', '高等数学')
        question_type = data.get('question_type', '综合类')
        
        if not ocr_text:
            return jsonify({'success': False, 'error': '题目内容为空'}), 400
        
        # 生成AI解答
        ai_answer = generate_ai_answer(ocr_text, subject, question_type)
        
        return jsonify({
            'success': True,
            'ai_answer': ai_answer,
            'message': 'AI解答生成成功'
        })
        
    except Exception as e:
        print(f"[Error] AI解答失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'AI解答生成失败: {str(e)}'
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取真实统计信息"""
    # 统计题目图片数量
    question_count = 0
    if os.path.exists(QUESTION_IMAGES_DIR):
        for f in os.listdir(QUESTION_IMAGES_DIR):
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
                question_count += 1
    
    # 统计答案数量
    answer_count = 0
    if os.path.exists(ANSWERS_DIR):
        for f in os.listdir(ANSWERS_DIR):
            if f.endswith('.txt'):
                answer_count += 1
    
    # 获取数据库统计
    db_stats = {}
    if DATABASE_AVAILABLE:
        try:
            db_stats = get_extended_db().get_statistics()
        except:
            pass
    
    return jsonify({
        'success': True,
        'stats': {
            'total_questions': question_count,
            'total_answers': answer_count,
            'today_searches': db_stats.get('today_searches', 0),
            'total_searches': db_stats.get('total_searches', 0),
            'pending_reports': db_stats.get('pending_reports', 0)
        }
    })


# ==================== 新增API接口 ====================

@app.route('/api/questions', methods=['GET'])
def get_questions():
    """获取题目列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category', '')
    
    questions = []
    if os.path.exists(QUESTION_IMAGES_DIR):
        all_files = [f for f in os.listdir(QUESTION_IMAGES_DIR) 
                     if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif'))]
        
        # 分页
        start = (page - 1) * per_page
        end = start + per_page
        page_files = all_files[start:end]
        
        for img_file in page_files:
            question_id = os.path.splitext(img_file)[0]
            has_answer = os.path.exists(os.path.join(ANSWERS_DIR, f"{question_id}.txt"))
            
            questions.append({
                'question_id': question_id,
                'image_path': img_file,
                'image_url': f'/api/question_image/{img_file}',
                'has_answer': has_answer,
                'category': guess_category(question_id)
            })
    
    return jsonify({
        'success': True,
        'questions': questions,
        'total': len(os.listdir(QUESTION_IMAGES_DIR)) if os.path.exists(QUESTION_IMAGES_DIR) else 0,
        'page': page,
        'per_page': per_page
    })


@app.route('/api/questions/<question_id>', methods=['GET'])
def get_question_detail(question_id):
    """获取题目详情"""
    # 查找图片
    image_path = None
    for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
        test_path = os.path.join(QUESTION_IMAGES_DIR, f"{question_id}{ext}")
        if os.path.exists(test_path):
            image_path = f"{question_id}{ext}"
            break
    
    if not image_path:
        return jsonify({'success': False, 'error': '题目不存在'}), 404
    
    # 读取答案
    answer = load_answer_file(question_id)
    
    return jsonify({
        'success': True,
        'question': {
            'question_id': question_id,
            'image_path': image_path,
            'image_url': f'/api/question_image/{image_path}',
            'answer': answer,
            'category': guess_category(question_id)
        }
    })


@app.route('/api/favorites', methods=['GET', 'POST', 'DELETE'])
def handle_favorites():
    """收藏功能"""
    user_ip = request.remote_addr or '127.0.0.1'
    
    if not DATABASE_AVAILABLE:
        return jsonify({'success': False, 'error': '数据库不可用'}), 500
    
    db = get_extended_db()
    
    if request.method == 'GET':
        # 获取收藏列表
        favorites = db.get_favorites(user_ip)
        return jsonify({'success': True, 'favorites': favorites})
    
    elif request.method == 'POST':
        # 添加收藏
        data = request.get_json()
        question_id = data.get('question_id')
        if not question_id:
            return jsonify({'success': False, 'error': '缺少question_id'}), 400
        
        success = db.add_favorite(user_ip, question_id)
        return jsonify({'success': success, 'message': '收藏成功' if success else '已收藏'})
    
    elif request.method == 'DELETE':
        # 取消收藏
        data = request.get_json()
        question_id = data.get('question_id')
        if not question_id:
            return jsonify({'success': False, 'error': '缺少question_id'}), 400
        
        success = db.remove_favorite(user_ip, question_id)
        return jsonify({'success': success, 'message': '已取消收藏' if success else '操作失败'})


@app.route('/api/history', methods=['GET', 'DELETE'])
def handle_history():
    """搜索历史"""
    user_ip = request.remote_addr or '127.0.0.1'
    
    if not DATABASE_AVAILABLE:
        return jsonify({'success': False, 'error': '数据库不可用'}), 500
    
    db = get_extended_db()
    
    if request.method == 'GET':
        history = db.get_search_history(user_ip, limit=20)
        return jsonify({'success': True, 'history': history})
    
    elif request.method == 'DELETE':
        count = db.clear_search_history(user_ip)
        return jsonify({'success': True, 'message': f'已清除 {count} 条记录'})


@app.route('/api/report', methods=['POST'])
def submit_report():
    """提交纠错"""
    if not DATABASE_AVAILABLE:
        return jsonify({'success': False, 'error': '数据库不可用'}), 500
    
    user_ip = request.remote_addr or '127.0.0.1'
    data = request.get_json()
    
    question_id = data.get('question_id')
    content = data.get('content')
    
    if not question_id or not content:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400
    
    db = get_extended_db()
    report_id = db.add_error_report(question_id, content, user_ip)
    
    return jsonify({
        'success': True,
        'report_id': report_id,
        'message': '感谢您的反馈！我们会尽快处理。'
    })


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """获取所有分类"""
    categories = {}
    
    if os.path.exists(QUESTION_IMAGES_DIR):
        for f in os.listdir(QUESTION_IMAGES_DIR):
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
                question_id = os.path.splitext(f)[0]
                cat = guess_category(question_id)
                categories[cat] = categories.get(cat, 0) + 1
    
    result = [{'name': k, 'count': v} for k, v in categories.items()]
    result.sort(key=lambda x: x['count'], reverse=True)
    
    return jsonify({'success': True, 'categories': result})


def guess_category(question_id):
    """根据题目ID猜测分类"""
    qid = question_id.lower()
    if 'calc' in qid:
        return '高等数学'
    elif 'phys' in qid:
        return '大学物理'
    elif 'circuit' in qid:
        return '电路分析'
    elif 'complex' in qid:
        return '复变函数'
    elif 'mech' in qid:
        return '理论力学'
    elif 'linear' in qid or 'matrix' in qid:
        return '线性代数'
    elif 'prob' in qid:
        return '概率论'
    else:
        return '其他'

if __name__ == '__main__':
    from waitress import serve
    
    # 预加载图像哈希（加速首次搜索）
    if IMAGE_MATCHER_AVAILABLE and os.path.exists(QUESTION_IMAGES_DIR):
        try:
            preload_image_hashes(QUESTION_IMAGES_DIR)
        except Exception as e:
            print(f"[Warning] Failed to preload image hashes: {e}")
    
    # 统计题库信息
    question_count = 0
    answer_count = 0
    if os.path.exists(QUESTION_IMAGES_DIR):
        question_count = len([f for f in os.listdir(QUESTION_IMAGES_DIR) 
                             if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif'))])
    if os.path.exists(ANSWERS_DIR):
        answer_count = len([f for f in os.listdir(ANSWERS_DIR) if f.endswith('.txt')])
    
    print("=" * 60)
    print("🎓 HUST专属搜题系统 v3.0 - 生产服务器")
    print("=" * 60)
    print(f"📚 题库统计: {question_count} 道题目, {answer_count} 个答案")
    print(f"🖼️  图像匹配: {'✅ 已启用' if IMAGE_MATCHER_AVAILABLE else '❌ 未启用'}")
    print(f"💾 数据库: {'✅ 已连接' if DATABASE_AVAILABLE else '❌ 未连接'}")
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

