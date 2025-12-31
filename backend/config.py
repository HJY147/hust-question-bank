"""
配置管理模块
从环境变量和.env文件加载配置
"""
import os
from pathlib import Path
from typing import Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
BASE_DIR = str(PROJECT_ROOT)  # 兼容旧代码

def load_env_file():
    """加载.env文件到环境变量"""
    env_file = PROJECT_ROOT / '.env'
    if not env_file.exists():
        print(f"⚠️  未找到.env文件，将使用默认配置")
        print(f"📝 请复制 .env.template 为 .env 并填入API密钥")
        return
    
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过注释和空行
            if not line or line.startswith('#'):
                continue
            # 解析 KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # 只在环境变量未设置时才设置
                if key and not os.getenv(key):
                    os.environ[key] = value

# 自动加载.env文件
load_env_file()

# 数据目录（兼容旧代码）
DATA_DIR = os.path.join(BASE_DIR, 'data')
QUESTION_BANK_DIR = os.path.join(DATA_DIR, 'question_bank')
ANSWERS_DIR = os.path.join(DATA_DIR, 'answers')
DATABASE_PATH = os.path.join(DATA_DIR, 'database.db')

# OCR 配置
OCR_CONFIG = {
    'use_angle_cls': True,  # 使用方向分类器
    'lang': 'ch',  # 中文识别
    'use_gpu': True,  # 使用GPU加速（如果可用）
    'det_db_thresh': 0.3,  # 检测阈值
    'det_db_box_thresh': 0.5,  # 文本框阈值
}

# 数学公式识别配置
MATH_OCR_CONFIG = {
    'enable': True,  # 启用公式识别
    'model_name': 'pix2tex',  # 公式识别模型
}

# 图像预处理配置
IMAGE_PREPROCESS = {
    'resize': (800, 1200),  # 调整大小
    'denoise': True,  # 去噪
    'enhance_contrast': True,  # 增强对比度
    'binarize': False,  # 二值化（可选）
}

# 匹配算法配置
MATCHING_CONFIG = {
    'similarity_threshold': 0.75,  # 相似度阈值（0-1）
    'text_weight': 0.7,  # 文本匹配权重
    'image_weight': 0.3,  # 图像匹配权重
    'top_k': 5,  # 返回前K个最相似结果
}

# 文本向量化模型
TEXT_EMBEDDING_MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'

# 图像特征提取模型
IMAGE_FEATURE_MODEL = 'resnet50'  # 可选：resnet50, vgg16, efficientnet

# ========== AI配置类 ==========
class Config:
    """AI和ML配置类"""
    
    # ========== DeepSeek配置 ==========
    DEEPSEEK_API_KEY: str = os.getenv('DEEPSEEK_API_KEY', '')
    DEEPSEEK_BASE_URL: str = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
    
    # ========== 豆包配置 ==========
    DOUBAO_API_KEY: str = os.getenv('DOUBAO_API_KEY', '')
    DOUBAO_ENDPOINT_ID: str = os.getenv('DOUBAO_ENDPOINT_ID', '')
    DOUBAO_REGION: str = os.getenv('DOUBAO_REGION', 'cn-beijing')
    
    # ========== AI功能开关 ==========
    AI_FALLBACK_THRESHOLD: float = float(os.getenv('AI_FALLBACK_THRESHOLD', '0.6'))
    AI_TIMEOUT: int = int(os.getenv('AI_TIMEOUT', '15'))  # 优化：减少超时时间到15秒，加快响应
    ENABLE_AI_SOLVER: bool = os.getenv('ENABLE_AI_SOLVER', 'true').lower() == 'true'
    ENABLE_IMAGE_OCR: bool = os.getenv('ENABLE_IMAGE_OCR', 'true').lower() == 'true'
    
    # ========== 性能优化配置 ==========
    MAX_TOKENS: int = int(os.getenv('MAX_TOKENS', '1200'))  # 减少token数量加快生成
    AI_TEMPERATURE: float = float(os.getenv('AI_TEMPERATURE', '0.1'))  # 降低随机性提高速度
    STREAM_RESPONSE: bool = os.getenv('STREAM_RESPONSE', 'false').lower() == 'true'  # 流式响应
    
    # ========== 机器学习配置 ==========
    ENABLE_ML_MATCHING: bool = os.getenv('ENABLE_ML_MATCHING', 'true').lower() == 'true'
    ML_MIN_SAMPLES: int = int(os.getenv('ML_MIN_SAMPLES', '10'))
    ML_TEXT_WEIGHT: float = float(os.getenv('ML_TEXT_WEIGHT', '0.6'))
    ML_IMAGE_WEIGHT: float = float(os.getenv('ML_IMAGE_WEIGHT', '0.4'))
    
    # ========== 文件路径配置 ==========
    DB_PATH: Path = PROJECT_ROOT / 'data' / 'questions.db'
    QUESTION_BANK_DIR_PATH: Path = PROJECT_ROOT / 'data' / 'question_bank'
    ANSWERS_DIR_PATH: Path = PROJECT_ROOT / 'data' / 'answers'
    UPLOAD_DIR: Path = PROJECT_ROOT / 'data' / 'uploads'
    ML_MODEL_DIR: Path = PROJECT_ROOT / 'data' / 'ml_models'
    
    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        验证配置是否完整
        
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        # 检查DeepSeek配置
        if cls.ENABLE_AI_SOLVER:
            if not cls.DEEPSEEK_API_KEY or cls.DEEPSEEK_API_KEY == 'your_deepseek_api_key_here':
                errors.append("DeepSeek API密钥未配置")
        
        # 检查豆包配置
        if cls.ENABLE_IMAGE_OCR:
            if not cls.DOUBAO_API_KEY or cls.DOUBAO_API_KEY == 'your_doubao_api_key_here':
                errors.append("豆包 API密钥未配置")
            if not cls.DOUBAO_ENDPOINT_ID or cls.DOUBAO_ENDPOINT_ID == 'your_endpoint_id_here':
                errors.append("豆包 Endpoint ID未配置")
        
        # 检查目录
        for dir_path in [cls.QUESTION_BANK_DIR_PATH, cls.ANSWERS_DIR_PATH, cls.UPLOAD_DIR, cls.ML_MODEL_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        return len(errors) == 0, errors
    
    @classmethod
    def print_status(cls):
        """打印配置状态"""
        print("\n" + "="*60)
        print("📋 系统配置状态")
        print("="*60)
        
        # AI功能状态
        print("\n🤖 AI功能:")
        print(f"  DeepSeek解答: {'✅ 启用' if cls.ENABLE_AI_SOLVER else '❌ 禁用'}")
        if cls.ENABLE_AI_SOLVER:
            print(f"    API密钥: {'✅ 已配置' if cls.DEEPSEEK_API_KEY and cls.DEEPSEEK_API_KEY != 'your_deepseek_api_key_here' else '❌ 未配置'}")
        
        print(f"  豆包图像识别: {'✅ 启用' if cls.ENABLE_IMAGE_OCR else '❌ 禁用'}")
        if cls.ENABLE_IMAGE_OCR:
            print(f"    API密钥: {'✅ 已配置' if cls.DOUBAO_API_KEY and cls.DOUBAO_API_KEY != 'your_doubao_api_key_here' else '❌ 未配置'}")
        
        print(f"  AI触发阈值: {cls.AI_FALLBACK_THRESHOLD}")
        
        # 机器学习状态
        print(f"\n🧠 机器学习:")
        print(f"  增强匹配: {'✅ 启用' if cls.ENABLE_ML_MATCHING else '❌ 禁用'}")
        print(f"  最小样本数: {cls.ML_MIN_SAMPLES}")
        print(f"  文本权重: {cls.ML_TEXT_WEIGHT}")
        print(f"  图像权重: {cls.ML_IMAGE_WEIGHT}")
        
        # 验证配置
        is_valid, errors = cls.validate()
        print(f"\n🔍 配置验证: {'✅ 通过' if is_valid else '❌ 失败'}")
        if errors:
            print("  错误信息:")
            for error in errors:
                print(f"    • {error}")
        
        print("="*60 + "\n")

# 创建全局配置实例
config = Config()

if __name__ == '__main__':
    # 测试配置
    config.print_status()

# CLIP 模型配置 (用于图文联合理解)
CLIP_CONFIG = {
    'model_name': 'ViT-B-32',  # 可选: ViT-B-32, ViT-L-14, ViT-H-14
    'pretrained': 'laion2b_s34b_b79k',  # 预训练权重
    'enable': True,  # 是否启用CLIP
}

# Ollama 配置 (本地LLM增强)
OLLAMA_CONFIG = {
    'base_url': 'http://localhost:11434',  # Ollama服务地址
    'model': 'qwen2:7b',  # 推荐使用的模型: qwen2:7b, llama3:8b, mistral
    'timeout': 60,  # 超时时间(秒)
    'enable': True,  # 是否启用Ollama增强
}

# Flask 配置
FLASK_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True,
}

# 上传文件配置
UPLOAD_CONFIG = {
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'allowed_extensions': {'png', 'jpg', 'jpeg', 'bmp', 'gif'},
    'upload_folder': os.path.join(DATA_DIR, 'uploads'),
}

# 确保目录存在
os.makedirs(QUESTION_BANK_DIR, exist_ok=True)
os.makedirs(ANSWERS_DIR, exist_ok=True)
os.makedirs(UPLOAD_CONFIG['upload_folder'], exist_ok=True)
