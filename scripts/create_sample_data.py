"""
创建示例题库
用于快速测试系统功能
"""
import os
import sys

# Ensure project root and backend directory are on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from backend.database import QuestionDatabase
from backend.config import QUESTION_BANK_DIR, ANSWERS_DIR


def create_sample_questions():
    """创建示例题目数据"""
    
    # 示例题目（模拟OCR识别结果）
    sample_questions = [
        {
            'question_id': 'calculus_001',
            'ocr_text': '求函数 f(x) = x³ - 3x² + 2 的极值点和极值',
            'category': 'calculus',
            'difficulty': 'medium',
            'tags': ['导数', '极值', '微分学'],
            'answer': '''
## 解答

**第一步：求导数**
$$f'(x) = 3x^2 - 6x = 3x(x-2)$$

**第二步：令导数为0**
$$3x(x-2) = 0$$
解得：$x_1 = 0$, $x_2 = 2$

**第三步：判断极值类型**
- 当 $x < 0$ 时，$f'(x) > 0$，函数递增
- 当 $0 < x < 2$ 时，$f'(x) < 0$，函数递减
- 当 $x > 2$ 时，$f'(x) > 0$，函数递增

**结论：**
- $x = 0$ 是极大值点，极大值 $f(0) = 2$
- $x = 2$ 是极小值点，极小值 $f(2) = -2$
''',
        },
        {
            'question_id': 'calculus_002',
            'ocr_text': '计算定积分 ∫₀¹ x²eˣ dx',
            'category': 'calculus',
            'difficulty': 'hard',
            'tags': ['定积分', '分部积分'],
            'answer': '''
## 解答

使用分部积分法，设 $u = x^2$, $dv = e^x dx$

**第一次分部积分：**
$$\\int x^2 e^x dx = x^2 e^x - 2\\int x e^x dx$$

**第二次分部积分：**
$$\\int x e^x dx = x e^x - \\int e^x dx = x e^x - e^x$$

**代入计算：**
$$\\int x^2 e^x dx = x^2 e^x - 2(x e^x - e^x) = x^2 e^x - 2x e^x + 2e^x$$

**代入上下限：**
$$\\int_0^1 x^2 e^x dx = [e^x(x^2 - 2x + 2)]_0^1 = e(1-2+2) - 1(0-0+2) = e - 2$$

**答案：** $\\boxed{e - 2}$
''',
        },
        {
            'question_id': 'physics_001',
            'ocr_text': '一个质量为2kg的物体从高度10m处自由下落，求落地时的速度（g=10m/s²）',
            'category': 'physics',
            'difficulty': 'easy',
            'tags': ['自由落体', '力学'],
            'answer': '''
## 解答

**已知条件：**
- 质量 $m = 2\\text{kg}$
- 高度 $h = 10\\text{m}$
- 重力加速度 $g = 10\\text{m/s}^2$
- 初速度 $v_0 = 0$

**方法一：运动学公式**
$$v^2 = v_0^2 + 2gh = 0 + 2 \\times 10 \\times 10 = 200$$
$$v = \\sqrt{200} = 10\\sqrt{2} \\approx 14.14\\text{m/s}$$

**方法二：能量守恒**
$$mgh = \\frac{1}{2}mv^2$$
$$v = \\sqrt{2gh} = \\sqrt{2 \\times 10 \\times 10} = 10\\sqrt{2}\\text{m/s}$$

**答案：** $\\boxed{10\\sqrt{2} \\approx 14.14\\text{m/s}}$
''',
        },
        {
            'question_id': 'complex_001',
            'ocr_text': '求复数 z = (1+i)⁴ 的值',
            'category': 'complex_analysis',
            'difficulty': 'medium',
            'tags': ['复数', '复数运算'],
            'answer': '''
## 解答

**方法一：直接计算**

首先计算 $(1+i)^2$：
$$(1+i)^2 = 1 + 2i + i^2 = 1 + 2i - 1 = 2i$$

然后计算 $(2i)^2$：
$$(1+i)^4 = (2i)^2 = 4i^2 = -4$$

**方法二：极坐标形式**

$1+i$ 的极坐标形式：
$$1+i = \\sqrt{2}e^{i\\pi/4}$$

因此：
$$(1+i)^4 = (\\sqrt{2})^4 e^{i\\pi} = 4e^{i\\pi} = 4(\\cos\\pi + i\\sin\\pi) = -4$$

**答案：** $\\boxed{-4}$
''',
        },
        {
            'question_id': 'circuit_001',
            'ocr_text': '一个电阻R=10Ω与电容C=100μF串联，接在电压U=220V、频率f=50Hz的交流电源上，求电路中的电流',
            'category': 'circuit',
            'difficulty': 'medium',
            'tags': ['交流电路', 'RC串联', '阻抗'],
            'answer': '''
## 解答

**已知条件：**
- 电阻 $R = 10\\Omega$
- 电容 $C = 100\\mu F = 100 \\times 10^{-6}F$
- 电压 $U = 220V$
- 频率 $f = 50Hz$

**第一步：计算容抗**
$$X_C = \\frac{1}{2\\pi fC} = \\frac{1}{2\\pi \\times 50 \\times 100 \\times 10^{-6}} = \\frac{1}{0.0314} \\approx 31.85\\Omega$$

**第二步：计算总阻抗**
$$Z = \\sqrt{R^2 + X_C^2} = \\sqrt{10^2 + 31.85^2} = \\sqrt{100 + 1014.4} \\approx 33.4\\Omega$$

**第三步：计算电流**
$$I = \\frac{U}{Z} = \\frac{220}{33.4} \\approx 6.59A$$

**答案：** $\\boxed{I \\approx 6.59A}$
''',
        },
        {
            'question_id': 'mechanics_001',
            'ocr_text': '一根长度为L、质量为m的均匀细杆，一端固定可绕该端转动，初始时水平静止，求释放后杆转过θ角时的角速度',
            'category': 'mechanics',
            'difficulty': 'hard',
            'tags': ['刚体动力学', '转动惯量', '能量守恒'],
            'answer': '''
## 解答

**分析：** 使用能量守恒定理

**第一步：计算转动惯量**
绕一端转动的均匀细杆：
$$I = \\frac{1}{3}mL^2$$

**第二步：计算质心下降高度**
质心在杆中点，下降高度为：
$$h = \\frac{L}{2}\\sin\\theta$$

**第三步：能量守恒**
重力势能转化为转动动能：
$$mg \\cdot \\frac{L}{2}\\sin\\theta = \\frac{1}{2}I\\omega^2$$

$$mg \\cdot \\frac{L}{2}\\sin\\theta = \\frac{1}{2} \\cdot \\frac{1}{3}mL^2 \\cdot \\omega^2$$

**第四步：求解角速度**
$$\\omega^2 = \\frac{3g\\sin\\theta}{L}$$

$$\\omega = \\sqrt{\\frac{3g\\sin\\theta}{L}}$$

**答案：** $\\boxed{\\omega = \\sqrt{\\frac{3g\\sin\\theta}{L}}}$
''',
        },
    ]
    
    return sample_questions


def import_sample_data():
    """导入示例数据到数据库"""
    print("=" * 50)
    print("  创建示例题库")
    print("=" * 50)
    
    # 初始化数据库
    db = QuestionDatabase()
    print("\n✓ 数据库已初始化")
    
    # 获取示例题目
    questions = create_sample_questions()
    
    imported = 0
    
    for q in questions:
        try:
            # 创建占位图片路径（实际使用时需要真实图片）
            image_path = os.path.join(QUESTION_BANK_DIR, f"{q['question_id']}.jpg")
            
            # 保存答案文件
            answer_path = os.path.join(ANSWERS_DIR, f"{q['question_id']}.txt")
            with open(answer_path, 'w', encoding='utf-8') as f:
                f.write(q['answer'])
            
            # 准备题目数据
            question_data = {
                'question_id': q['question_id'],
                'image_path': image_path,  # 占位
                'answer_path': answer_path,
                'ocr_text': q['ocr_text'],
                'category': q['category'],
                'difficulty': q['difficulty'],
                'tags': q['tags'],
                'text_embedding': None,  # 稍后生成
                'image_embedding': None,
            }
            
            # 尝试生成文本嵌入
            try:
                from sentence_transformers import SentenceTransformer
                from backend.config import TEXT_EMBEDDING_MODEL
                import numpy as np
                
                model = SentenceTransformer(TEXT_EMBEDDING_MODEL)
                embedding = model.encode(q['ocr_text'], convert_to_numpy=True)
                question_data['text_embedding'] = embedding.astype(np.float32)
            except Exception as e:
                print(f"  ⚠ 文本嵌入生成失败: {e}")
            
            # 插入数据库
            db.insert_question(question_data)
            print(f"  ✓ 导入: {q['question_id']} ({q['category']})")
            imported += 1
            
        except Exception as e:
            print(f"  ✗ 导入失败 {q['question_id']}: {e}")
    
    print(f"\n导入完成：{imported}/{len(questions)} 道题目")
    print("\n注意：示例数据使用模拟的OCR文本，没有真实图片。")
    print("要完整使用系统，请按照 COMPLETE_WORKFLOW.md 准备真实的题目图片。")
    print("=" * 50)


if __name__ == '__main__':
    import_sample_data()
