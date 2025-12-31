"""
生成真实的数学题目示例图片
使用 PIL 绘制题目文字和公式
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from backend.config import QUESTION_BANK_DIR, ANSWERS_DIR

# 示例题目数据
SAMPLE_QUESTIONS = [
    {
        'id': 'calc_001',
        'question': '求函数 f(x) = x^3 - 3x^2 + 2\n在区间 [0, 3] 上的最大值和最小值',
        'answer': '''解：
1. 求导数：f'(x) = 3x^2 - 6x = 3x(x - 2)
2. 令 f'(x) = 0，得驻点：x = 0, x = 2
3. 计算函数值：
   f(0) = 2
   f(2) = 8 - 12 + 2 = -2
   f(3) = 27 - 27 + 2 = 2
4. 结论：最大值为 2（在 x=0 和 x=3 处），最小值为 -2（在 x=2 处）
''',
        'category': 'calculus'
    },
    {
        'id': 'calc_004',
        'question': '求极限：\nlim(x→∞) (2x^2 + 3x - 1) / (x^2 - 5)',
        'answer': '''解：
这是∞/∞型不定式，分子分母同除以x^2：

lim(x→∞) (2x^2 + 3x - 1) / (x^2 - 5)
= lim(x→∞) (2 + 3/x - 1/x^2) / (1 - 5/x^2)

当 x→∞ 时：
- 3/x → 0
- 1/x^2 → 0
- 5/x^2 → 0

因此：
= (2 + 0 - 0) / (1 - 0)
= 2/1
= 2

答案：2
''',
        'category': 'calculus'
    },
    {
        'id': 'calc_005',
        'question': '求不定积分：\n∫ x·e^x dx',
        'answer': '''解：
使用分部积分法：∫ u dv = uv - ∫ v du

令：u = x,  dv = e^x dx
则：du = dx,  v = e^x

代入公式：
∫ x·e^x dx = x·e^x - ∫ e^x dx
           = x·e^x - e^x + C
           = e^x(x - 1) + C

答案：e^x(x - 1) + C
''',
        'category': 'calculus'
    },
    {
        'id': 'calc_002',
        'question': '计算定积分：\n∫[0,π] sin(x) dx',
        'answer': '''解：
∫ sin(x) dx = -cos(x) + C

代入上下限：
[-cos(x)]₀^π = -cos(π) - (-cos(0))
           = -(-1) - (-1)
           = 1 + 1
           = 2

答案：2
''',
        'category': 'calculus'
    },
    {
        'id': 'phys_001',
        'question': '一质点做简谐运动，振幅 A = 0.1m，\n周期 T = 2s，初相位 φ = 0。\n求：(1) 运动方程  (2) t=0.5s 时的位移',
        'answer': '''解：
(1) 简谐运动方程：x = A·cos(ωt + φ)
    角频率：ω = 2π/T = 2π/2 = π rad/s
    运动方程：x = 0.1·cos(πt) (m)

(2) t = 0.5s 时：
    x = 0.1·cos(π×0.5)
      = 0.1·cos(π/2)
      = 0.1 × 0
      = 0 (m)

答案：(1) x = 0.1cos(πt) m  (2) x = 0 m
''',
        'category': 'physics'
    },
    {
        'id': 'phys_002',
        'question': '一个质量为 m = 2kg 的物体，\n受到 F = 10N 的恒力作用，\n从静止开始运动。求 5s 后的速度。',
        'answer': '''解：
由牛顿第二定律：F = ma
加速度：a = F/m = 10/2 = 5 m/s²

匀加速直线运动速度公式：v = v₀ + at
初速度 v₀ = 0，时间 t = 5s

代入：v = 0 + 5×5 = 25 m/s

答案：25 m/s
''',
        'category': 'physics'
    },
    {
        'id': 'phys_003',
        'question': '一个单摆，摆长 L = 1m，\n在地球表面（g = 10m/s²）\n求周期 T',
        'answer': '''解：
单摆周期公式：T = 2π√(L/g)

代入数据：
T = 2π√(1/10)
  = 2π√0.1
  = 2π × 0.316
  ≈ 2π × 1/√10
  ≈ 2 × 3.14 × 0.316
  ≈ 2.0 s

答案：T ≈ 2.0 s
''',
        'category': 'physics'
    },
    {
        'id': 'phys_004',
        'question': '一个物体做匀速圆周运动，\n半径 r = 2m，线速度 v = 4m/s\n求角速度 ω 和周期 T',
        'answer': '''解：
(1) 线速度与角速度关系：v = ωr
    角速度：ω = v/r = 4/2 = 2 rad/s

(2) 周期与角速度关系：T = 2π/ω
    周期：T = 2π/2 = π s ≈ 3.14 s

答案：ω = 2 rad/s, T = π s ≈ 3.14 s
''',
        'category': 'physics'
    },
    {
        'id': 'complex_001',
        'question': '求复数 z = (1+i)/(1-i) 的模和辐角',
        'answer': '''解：
(1) 化简复数：
    z = (1+i)/(1-i)
      = (1+i)(1+i)/[(1-i)(1+i)]
      = (1+2i+i²)/(1-i²)
      = (1+2i-1)/(1+1)
      = 2i/2
      = i

(2) 模：|z| = |i| = 1

(3) 辐角：arg(z) = π/2 (或 90°)

答案：|z| = 1, arg(z) = π/2
''',
        'category': 'complex_analysis'
    },
    {
        'id': 'complex_002',
        'question': '已知 z₁ = 3 + 4i, z₂ = 1 - 2i\n求 z₁ + z₂ 和 z₁ × z₂',
        'answer': '''解：
(1) z₁ + z₂ = (3 + 4i) + (1 - 2i)
             = (3 + 1) + (4 - 2)i
             = 4 + 2i

(2) z₁ × z₂ = (3 + 4i)(1 - 2i)
             = 3 - 6i + 4i - 8i²
             = 3 - 2i - 8(-1)
             = 3 - 2i + 8
             = 11 - 2i

答案：z₁ + z₂ = 4 + 2i, z₁ × z₂ = 11 - 2i
''',
        'category': 'complex_analysis'
    },
    {
        'id': 'circuit_001',
        'question': '串联电路中，R1=10Ω，R2=20Ω，\n电源电压 U=30V。\n求：(1) 总电阻  (2) 电路电流  (3) R1 两端电压',
        'answer': '''解：
(1) 串联电路总电阻：
    R总 = R1 + R2 = 10 + 20 = 30 Ω

(2) 欧姆定律求电流：
    I = U/R总 = 30/30 = 1 A

(3) R1 两端电压：
    U1 = I × R1 = 1 × 10 = 10 V

答案：(1) 30Ω  (2) 1A  (3) 10V
''',
        'category': 'circuit'
    },
    {
        'id': 'circuit_002',
        'question': '并联电路中，R1=6Ω，R2=12Ω，\n电源电压 U=12V。\n求总电阻和各支路电流',
        'answer': '''解：
(1) 并联电路总电阻：
    1/R总 = 1/R1 + 1/R2
    1/R总 = 1/6 + 1/12 = 2/12 + 1/12 = 3/12
    R总 = 12/3 = 4 Ω

(2) 各支路电流：
    I1 = U/R1 = 12/6 = 2 A
    I2 = U/R2 = 12/12 = 1 A

(3) 总电流：
    I = I1 + I2 = 2 + 1 = 3 A
    （验证：I = U/R总 = 12/4 = 3 A ✓）

答案：R总 = 4Ω, I1 = 2A, I2 = 1A
''',
        'category': 'circuit'
    },
    {
        'id': 'mech_001',
        'question': '一根长 L=2m 的均质杆，质量 m=10kg，\n绕一端转动。求转动惯量。\n(已知：细杆绕端点转动惯量 I=mL²/3)',
        'answer': '''解：
根据公式：I = mL²/3

代入数据：
I = (10 × 2²) / 3
  = (10 × 4) / 3
  = 40/3
  ≈ 13.33 kg·m²

答案：I = 40/3 kg·m² ≈ 13.33 kg·m²
''',
        'category': 'mechanics'
    },
    {
        'id': 'mech_002',
        'question': '质量 m=5kg 的物体，\n在光滑水平面上受力 F=20N，\n求加速度和3秒后的速度',
        'answer': '''解：
(1) 由牛顿第二定律：F = ma
    加速度：a = F/m = 20/5 = 4 m/s²

(2) 匀加速运动：v = v₀ + at
    初速度 v₀ = 0
    时间 t = 3s
    速度：v = 0 + 4×3 = 12 m/s

答案：a = 4 m/s², v = 12 m/s
''',
        'category': 'mechanics'
    },
    {
        'id': 'calc_003',
        'question': '求极限：\nlim(x→0) (sin x) / x',
        'answer': '''解：
这是重要极限之一。

方法一（直接应用重要极限）：
lim(x→0) (sin x) / x = 1

方法二（洛必达法则）：
当 x→0 时，分子分母都趋于 0，可用洛必达法则：
lim(x→0) (sin x) / x
= lim(x→0) (sin x)' / (x)'
= lim(x→0) cos x / 1
= cos 0
= 1

答案：1
''',
        'category': 'calculus'
    }
]


def create_question_image(question_text, output_path, width=800, height=400):
    """创建题目图片"""
    # 创建白色背景
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # 尝试使用中文字体，如果失败则使用默认字体
    try:
        # Windows 系统字体
        font_title = ImageFont.truetype('msyh.ttc', 32)  # 微软雅黑标题
        font_content = ImageFont.truetype('msyh.ttc', 24)  # 微软雅黑内容
    except:
        try:
            font_title = ImageFont.truetype('arial.ttf', 32)
            font_content = ImageFont.truetype('arial.ttf', 24)
        except:
            font_title = ImageFont.load_default()
            font_content = ImageFont.load_default()
    
    # 绘制"题目："标题
    draw.text((40, 30), "题目:", fill='black', font=font_title)
    
    # 绘制题目内容（多行处理）
    y_position = 80
    for line in question_text.split('\n'):
        draw.text((40, y_position), line, fill='black', font=font_content)
        y_position += 40
    
    # 保存图片
    img.save(output_path)
    print(f"✓ 生成图片: {output_path}")


def main():
    """生成所有示例题目"""
    # 创建目录
    os.makedirs(QUESTION_BANK_DIR, exist_ok=True)
    os.makedirs(ANSWERS_DIR, exist_ok=True)
    
    print("="*60)
    print("生成真实示例题目")
    print("="*60)
    
    for question in SAMPLE_QUESTIONS:
        # 生成题目图片
        image_path = os.path.join(QUESTION_BANK_DIR, f"{question['id']}.png")
        create_question_image(question['question'], image_path)
        
        # 保存答案文本
        answer_path = os.path.join(ANSWERS_DIR, f"{question['id']}.txt")
        with open(answer_path, 'w', encoding='utf-8') as f:
            f.write(question['answer'])
        print(f"✓ 保存答案: {answer_path}")
        
        print()
    
    print("="*60)
    print(f"完成！生成了 {len(SAMPLE_QUESTIONS)} 道题目")
    print(f"题目图片目录: {QUESTION_BANK_DIR}")
    print(f"答案文本目录: {ANSWERS_DIR}")
    print("="*60)
    print("\n下一步：运行 'python scripts/import_questions.py' 导入题库")


if __name__ == '__main__':
    main()
