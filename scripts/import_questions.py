"""
导入题目到数据库
从图片和答案文件创建题库
"""
import os
import sys
from pathlib import Path
import argparse

# Ensure project root and backend directory are on sys.path so imports like
# `from backend.database import ...` and backend modules importing `config`
# (which expects to be importable as a top-level module) work regardless
# of current working directory when running this script.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from backend.database import QuestionDatabase
from backend.ocr_service import get_ocr_service
from backend.matcher import QuestionMatcher
from backend.config import QUESTION_BANK_DIR, ANSWERS_DIR


def import_questions(
    question_dir: str, 
    answer_dir: str, 
    db: QuestionDatabase,
    ocr_service,
    matcher: QuestionMatcher,
    category: str = None
):
    """
    导入题目到数据库
    
    Args:
        question_dir: 题目图片目录
        answer_dir: 答案文本目录
        db: 数据库实例
        ocr_service: OCR服务实例
        matcher: 匹配器实例
        category: 题目类别（可选）
    """
    question_path = Path(question_dir)
    answer_path = Path(answer_dir)
    
    # 支持的图像格式
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    
    # 获取所有题目图片
    image_files = sorted([f for f in question_path.iterdir() 
                         if f.suffix.lower() in image_extensions])
    
    print(f"找到 {len(image_files)} 个题目图片")
    
    imported_count = 0
    failed_count = 0
    
    for i, image_file in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}] 处理: {image_file.name}")
        
        try:
            # 生成题目ID（从文件名提取，如 q001.jpg -> q001）
            question_id = image_file.stem
            
            # 检查是否已存在
            existing = db.get_question_by_id(question_id)
            if existing:
                print(f"  ⚠ 题目已存在，跳过: {question_id}")
                continue
            
            # 查找对应的答案文件
            answer_file = answer_path / f"{question_id}.txt"
            answer_text = None
            
            if answer_file.exists():
                try:
                    with open(answer_file, 'r', encoding='utf-8') as f:
                        answer_text = f.read().strip()
                    print(f"  ✓ 找到答案文件")
                except Exception as e:
                    print(f"  ⚠ 读取答案失败: {e}")
            else:
                print(f"  ⚠ 未找到答案文件: {answer_file.name}")
            
            # OCR 识别题目
            print(f"  → 正在识别题目...")
            ocr_result = ocr_service.recognize_image(str(image_file))
            ocr_text = ocr_result.get('text', '')
            
            if ocr_text:
                print(f"  ✓ OCR识别成功 (置信度: {ocr_result.get('confidence', 0):.2%})")
                print(f"    文本片段: {ocr_text[:50]}...")
            else:
                print(f"  ⚠ OCR识别失败或无文本")
            
            # 提取LaTeX公式
            latex_formulas = []
            for formula in ocr_result.get('formulas', []):
                latex_formulas.append(formula['latex'])
            
            latex_formula = ' '.join(latex_formulas) if latex_formulas else None
            
            # 提取文本嵌入
            print(f"  → 提取特征向量...")
            text_for_embedding = ocr_text
            if latex_formula:
                text_for_embedding += ' ' + latex_formula
            
            text_embedding = matcher.extract_text_embedding(text_for_embedding) if text_for_embedding else None
            
            # 提取图像嵌入
            image_embedding = matcher.extract_image_embedding(str(image_file))
            
            # 准备题目数据
            question_data = {
                'question_id': question_id,
                'image_path': str(image_file),
                'answer_path': str(answer_file) if answer_file.exists() else None,
                'ocr_text': ocr_text,
                'latex_formula': latex_formula,
                'text_embedding': text_embedding,
                'image_embedding': image_embedding,
                'category': category,
                'difficulty': None,
                'tags': [],
            }
            
            # 插入数据库
            db.insert_question(question_data)
            print(f"  ✓ 导入成功: {question_id}")
            
            imported_count += 1
            
        except Exception as e:
            print(f"  ✗ 导入失败: {e}")
            import traceback
            traceback.print_exc()
            failed_count += 1
    
    print(f"\n" + "="*50)
    print(f"导入完成!")
    print(f"  成功: {imported_count}")
    print(f"  失败: {failed_count}")
    print(f"  总计: {len(image_files)}")
    print("="*50)
    
    # 更新匹配器索引
    print("\n更新索引...")
    matcher.load_question_embeddings()
    print("索引更新完成!")


def main():
    parser = argparse.ArgumentParser(description='导入题目到数据库')
    parser.add_argument('--question-dir', '-q', 
                       default=QUESTION_BANK_DIR,
                       help='题目图片目录')
    parser.add_argument('--answer-dir', '-a',
                       default=ANSWERS_DIR,
                       help='答案文本目录')
    parser.add_argument('--category', '-c',
                       help='题目类别 (如: 微积分, 大学物理, 电路理论等)')
    
    args = parser.parse_args()
    
    # 检查目录
    if not os.path.exists(args.question_dir):
        print(f"错误: 题目目录不存在: {args.question_dir}")
        return
    
    if not os.path.exists(args.answer_dir):
        print(f"警告: 答案目录不存在: {args.answer_dir}")
        print(f"将创建目录: {args.answer_dir}")
        os.makedirs(args.answer_dir, exist_ok=True)
    
    # 初始化服务
    print("初始化服务...")
    db = QuestionDatabase()
    ocr_service = get_ocr_service()
    matcher = QuestionMatcher(db)
    
    print(f"\n当前题库中有 {db.count_questions()} 道题目\n")
    
    # 导入题目
    import_questions(
        question_dir=args.question_dir,
        answer_dir=args.answer_dir,
        db=db,
        ocr_service=ocr_service,
        matcher=matcher,
        category=args.category
    )


if __name__ == '__main__':
    main()
