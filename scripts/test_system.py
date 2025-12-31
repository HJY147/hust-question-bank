"""
快速测试脚本
用于验证系统各组件是否正常工作
"""
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_environment():
    """测试环境配置"""
    print("=" * 60)
    print("🔍 环境检测")
    print("=" * 60)
    
    # Python版本
    print(f"\nPython版本: {sys.version}")
    
    # PyTorch
    try:
        import torch
        print(f"✓ PyTorch: {torch.__version__}")
        print(f"  CUDA可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"  GPU: {torch.cuda.get_device_name(0)}")
    except ImportError:
        print("✗ PyTorch 未安装")
    
    # PaddlePaddle
    try:
        import paddle
        print(f"✓ PaddlePaddle: {paddle.__version__}")
    except ImportError:
        print("✗ PaddlePaddle 未安装")
    
    # PaddleOCR
    try:
        from paddleocr import PaddleOCR
        print("✓ PaddleOCR 可用")
    except ImportError:
        print("✗ PaddleOCR 未安装")
    
    # Sentence Transformers
    try:
        from sentence_transformers import SentenceTransformer
        print("✓ Sentence-Transformers 可用")
    except ImportError:
        print("✗ Sentence-Transformers 未安装")
    
    # CLIP
    try:
        import open_clip
        print("✓ OpenCLIP 可用")
    except ImportError:
        print("✗ OpenCLIP 未安装")
    
    # OpenCV
    try:
        import cv2
        print(f"✓ OpenCV: {cv2.__version__}")
    except ImportError:
        print("✗ OpenCV 未安装")
    
    print()


def test_ocr():
    """测试OCR功能"""
    print("=" * 60)
    print("📝 OCR识别测试")
    print("=" * 60)
    
    try:
        from backend.ocr_service import get_ocr_service
        
        ocr_service = get_ocr_service()
        print("✓ OCR服务初始化成功")
        
        # 测试识别（需要测试图片）
        test_image = "data/question_bank/test.jpg"
        if os.path.exists(test_image):
            result = ocr_service.recognize_image(test_image)
            print(f"✓ 识别测试成功")
            print(f"  文本: {result.get('text', '')[:100]}...")
            print(f"  置信度: {result.get('confidence', 0):.2%}")
        else:
            print(f"⚠ 测试图片不存在: {test_image}")
            print("  请将测试图片放入 data/question_bank/ 目录")
        
    except Exception as e:
        print(f"✗ OCR测试失败: {e}")
    
    print()


def test_matching():
    """测试匹配功能"""
    print("=" * 60)
    print("🔍 匹配功能测试")
    print("=" * 60)
    
    try:
        from backend.database import QuestionDatabase
        from backend.matcher import get_matcher
        
        db = QuestionDatabase()
        matcher = get_matcher(db)
        
        print("✓ 匹配器初始化成功")
        
        # 测试文本嵌入
        test_text = "求函数 f(x) = x^2 在 x=1 处的导数"
        embedding = matcher.extract_text_embedding(test_text)
        
        if embedding is not None:
            print(f"✓ 文本嵌入成功，维度: {embedding.shape}")
        else:
            print("⚠ 文本嵌入失败（可能是模型未加载）")
        
    except Exception as e:
        print(f"✗ 匹配测试失败: {e}")
    
    print()


def test_clip():
    """测试CLIP功能"""
    print("=" * 60)
    print("🖼️ CLIP功能测试")
    print("=" * 60)
    
    try:
        from backend.clip_service import get_clip_service
        
        clip_service = get_clip_service()
        
        if clip_service.is_available():
            print("✓ CLIP服务初始化成功")
            
            # 测试分类
            test_image = "data/question_bank/test.jpg"
            if os.path.exists(test_image):
                result = clip_service.classify_image_type(test_image)
                print(f"✓ 图像分类测试成功")
                print(f"  类型: {result.get('type')}")
                print(f"  置信度: {result.get('confidence', 0):.2%}")
            else:
                print(f"⚠ 测试图片不存在: {test_image}")
        else:
            print("⚠ CLIP服务不可用")
        
    except Exception as e:
        print(f"✗ CLIP测试失败: {e}")
    
    print()


def test_ollama():
    """测试Ollama功能"""
    print("=" * 60)
    print("🤖 Ollama功能测试")
    print("=" * 60)
    
    try:
        from backend.ollama_service import get_ollama_service
        
        ollama_service = get_ollama_service()
        
        if ollama_service.is_available():
            print("✓ Ollama服务连接成功")
            
            # 列出可用模型
            models = ollama_service.list_models()
            print(f"  可用模型: {', '.join(models[:5])}")
            
            # 测试生成
            result = ollama_service.generate("1+1等于几？", "用一个数字回答")
            if result:
                print(f"✓ 生成测试成功: {result[:50]}")
        else:
            print("⚠ Ollama服务不可用")
            print("  请确保Ollama已启动: ollama serve")
        
    except Exception as e:
        print(f"✗ Ollama测试失败: {e}")
    
    print()


def test_database():
    """测试数据库"""
    print("=" * 60)
    print("💾 数据库测试")
    print("=" * 60)
    
    try:
        from backend.database import QuestionDatabase
        
        db = QuestionDatabase()
        print("✓ 数据库连接成功")
        
        # 获取题目数量
        questions = db.get_all_questions()
        print(f"  题库中有 {len(questions)} 道题目")
        
        if questions:
            q = questions[0]
            print(f"  示例题目ID: {q.get('question_id')}")
            print(f"  类别: {q.get('category')}")
        
    except Exception as e:
        print(f"✗ 数据库测试失败: {e}")
    
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("  📚 拍照搜题系统 - 组件测试")
    print("=" * 60 + "\n")
    
    test_environment()
    test_database()
    test_ocr()
    test_matching()
    test_clip()
    test_ollama()
    
    print("=" * 60)
    print("  测试完成！")
    print("=" * 60)
    print("\n如果所有组件都显示 ✓，系统已准备就绪。")
    print("如果有 ✗ 或 ⚠，请根据提示安装缺失的依赖。\n")


if __name__ == '__main__':
    main()
