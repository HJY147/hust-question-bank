"""
快速添加题目工具
交互式添加单个题目到题库
"""
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from backend.database import QuestionDatabase
from backend.matcher import QuestionMatcher


def print_banner():
    """打印欢迎信息"""
    print("\n" + "="*70)
    print("📝 快速添加题目工具".center(70))
    print("="*70 + "\n")


def get_input(prompt, required=True):
    """获取用户输入"""
    while True:
        value = input(prompt).strip()
        if value or not required:
            return value
        print("⚠ 此项不能为空，请重新输入。\n")


def select_category():
    """选择题目类别"""
    categories = {
        '1': ('calculus', '微积分'),
        '2': ('physics', '大学物理'),
        '3': ('circuit', '电路理论'),
        '4': ('complex_analysis', '复变函数'),
        '5': ('mechanics', '理论力学'),
        '6': ('linear_algebra', '线性代数'),
        '7': ('probability', '概率论'),
        '8': ('custom', '自定义'),
    }
    
    print("\n请选择题目类别：")
    for key, (eng, chn) in categories.items():
        print(f"  {key}. {chn} ({eng})")
    
    while True:
        choice = input("\n输入序号 (1-8): ").strip()
        if choice in categories:
            if choice == '8':
                custom = get_input("请输入自定义类别（英文）: ")
                return custom
            return categories[choice][0]
        print("⚠ 无效选择，请重新输入。")


def main():
    """主函数"""
    print_banner()
    
    print("欢迎使用快速添加题目工具！\n")
    print("提示：")
    print("  • 按 Ctrl+C 可随时退出")
    print("  • 多行输入时，输入空行表示结束")
    print("  • 建议先准备好题目和答案内容\n")
    
    try:
        # 初始化数据库
        print("正在初始化...")
        db = QuestionDatabase()
        matcher = QuestionMatcher(db)
        current_count = db.count_questions()
        print(f"✓ 当前题库：{current_count} 道题目\n")
        
        while True:
            print("\n" + "-"*70)
            print("📝 添加新题目")
            print("-"*70 + "\n")
            
            # 获取题目ID
            question_id = get_input("题目ID（如 calc_001）: ")
            
            # 检查是否已存在
            existing = db.get_question_by_id(question_id)
            if existing:
                print(f"\n⚠ 题目 {question_id} 已存在！")
                overwrite = input("是否覆盖？(y/n): ").strip().lower()
                if overwrite != 'y':
                    continue
                db.delete_question(question_id)
                print("✓ 已删除旧题目")
            
            # 选择类别
            category = select_category()
            
            # 获取题目内容
            print("\n请输入题目内容（多行输入，输入空行结束）：")
            question_lines = []
            while True:
                line = input()
                if not line:
                    break
                question_lines.append(line)
            question_text = '\n'.join(question_lines)
            
            if not question_text:
                print("⚠ 题目内容不能为空！")
                continue
            
            # 获取答案
            print("\n请输入答案内容（多行输入，输入空行结束）：")
            answer_lines = []
            while True:
                line = input()
                if not line:
                    break
                answer_lines.append(line)
            answer_text = '\n'.join(answer_lines)
            
            # 确认信息
            print("\n" + "="*70)
            print("📋 请确认题目信息：")
            print("="*70)
            print(f"\n题目ID: {question_id}")
            print(f"类别: {category}")
            print(f"\n题目内容:\n{question_text[:100]}{'...' if len(question_text) > 100 else ''}")
            print(f"\n答案:\n{answer_text[:100] if answer_text else '(无答案)'}{'...' if len(answer_text) > 100 else ''}")
            
            confirm = input("\n确认添加？(y/n): ").strip().lower()
            if confirm != 'y':
                print("❌ 已取消")
                continue
            
            # 提取文本嵌入
            print("\n正在处理...")
            text_embedding = matcher.extract_text_embedding(question_text)
            
            # 准备数据
            question_data = {
                'question_id': question_id,
                'image_path': None,
                'answer_path': None,
                'ocr_text': question_text,
                'latex_formula': None,
                'text_embedding': text_embedding,
                'image_embedding': None,
                'category': category,
                'difficulty': None,
                'tags': [],
            }
            
            # 插入数据库
            db.insert_question(question_data)
            
            # 保存答案到文件
            if answer_text:
                answers_dir = os.path.join(PROJECT_ROOT, 'data', 'answers')
                os.makedirs(answers_dir, exist_ok=True)
                answer_file = os.path.join(answers_dir, f"{question_id}.txt")
                with open(answer_file, 'w', encoding='utf-8') as f:
                    f.write(answer_text)
                print(f"✓ 答案已保存到: {answer_file}")
            
            # 更新索引
            matcher.load_question_embeddings()
            
            print(f"\n✅ 题目 {question_id} 添加成功！")
            print(f"当前题库：{db.count_questions()} 道题目")
            
            # 是否继续
            continue_add = input("\n是否继续添加？(y/n): ").strip().lower()
            if continue_add != 'y':
                break
        
        print("\n" + "="*70)
        print("🎉 完成！")
        print(f"题库总量：{db.count_questions()} 道题目")
        print("="*70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n👋 已退出")
    except Exception as e:
        print(f"\n❌ 出错了: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
