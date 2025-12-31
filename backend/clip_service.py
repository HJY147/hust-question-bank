"""
CLIP 图像-文本匹配服务
用于更好地理解包含图片的题目（电路图、力学图等）
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
import cv2
from PIL import Image

try:
    import open_clip
    import torch
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    print("Warning: open_clip not installed. CLIP功能将不可用")

from config import CLIP_CONFIG


class CLIPService:
    """CLIP 服务类 - 用于图像-文本联合理解"""
    
    def __init__(self):
        self.model = None
        self.preprocess = None
        self.tokenizer = None
        self.device = None
        self._initialized = False
        
        if CLIP_AVAILABLE:
            self._init_model()
    
    def _init_model(self):
        """初始化CLIP模型"""
        try:
            model_name = CLIP_CONFIG.get('model_name', 'ViT-B-32')
            pretrained = CLIP_CONFIG.get('pretrained', 'laion2b_s34b_b79k')
            
            # 选择设备
            if torch.cuda.is_available():
                self.device = 'cuda'
            else:
                self.device = 'cpu'
            
            print(f"加载CLIP模型: {model_name} (设备: {self.device})")
            
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                model_name, 
                pretrained=pretrained
            )
            self.model = self.model.to(self.device)
            self.model.eval()
            
            self.tokenizer = open_clip.get_tokenizer(model_name)
            
            self._initialized = True
            print("CLIP模型加载成功")
            
        except Exception as e:
            print(f"CLIP模型加载失败: {e}")
            self._initialized = False
    
    def is_available(self) -> bool:
        """检查CLIP是否可用"""
        return CLIP_AVAILABLE and self._initialized
    
    def extract_image_features(self, image_path: str) -> Optional[np.ndarray]:
        """
        提取图像特征向量
        
        Args:
            image_path: 图像路径
            
        Returns:
            特征向量 (归一化后的)
        """
        if not self.is_available():
            return None
        
        try:
            # 加载图像
            image = Image.open(image_path).convert('RGB')
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                image_features = self.model.encode_image(image_input)
                # 归一化
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy().astype(np.float32).flatten()
            
        except Exception as e:
            print(f"CLIP图像特征提取失败: {e}")
            return None
    
    def extract_text_features(self, text: str) -> Optional[np.ndarray]:
        """
        提取文本特征向量
        
        Args:
            text: 输入文本
            
        Returns:
            特征向量 (归一化后的)
        """
        if not self.is_available():
            return None
        
        try:
            # 文本编码
            text_input = self.tokenizer([text]).to(self.device)
            
            with torch.no_grad():
                text_features = self.model.encode_text(text_input)
                # 归一化
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            return text_features.cpu().numpy().astype(np.float32).flatten()
            
        except Exception as e:
            print(f"CLIP文本特征提取失败: {e}")
            return None
    
    def compute_similarity(
        self, 
        image_path: str = None, 
        query_text: str = None,
        target_image_features: np.ndarray = None,
        target_text_features: np.ndarray = None
    ) -> float:
        """
        计算查询与目标之间的相似度
        支持多种组合：
        - 图像vs图像
        - 文本vs文本
        - 图像vs文本（跨模态）
        
        Args:
            image_path: 查询图像路径
            query_text: 查询文本
            target_image_features: 目标图像特征
            target_text_features: 目标文本特征
            
        Returns:
            相似度分数 (0-1)
        """
        if not self.is_available():
            return 0.0
        
        query_features = None
        target_features = None
        
        # 提取查询特征
        if image_path:
            query_features = self.extract_image_features(image_path)
        elif query_text:
            query_features = self.extract_text_features(query_text)
        
        if query_features is None:
            return 0.0
        
        # 选择目标特征
        if target_image_features is not None:
            target_features = target_image_features
        elif target_text_features is not None:
            target_features = target_text_features
        
        if target_features is None:
            return 0.0
        
        # 计算余弦相似度
        similarity = np.dot(query_features, target_features)
        # CLIP的相似度通常需要缩放
        similarity = (similarity + 1) / 2  # 映射到0-1
        
        return float(similarity)
    
    def batch_compute_similarity(
        self, 
        image_path: str,
        target_features_list: List[np.ndarray]
    ) -> List[float]:
        """
        批量计算相似度
        
        Args:
            image_path: 查询图像路径
            target_features_list: 目标特征向量列表
            
        Returns:
            相似度分数列表
        """
        if not self.is_available() or not target_features_list:
            return [0.0] * len(target_features_list)
        
        query_features = self.extract_image_features(image_path)
        if query_features is None:
            return [0.0] * len(target_features_list)
        
        # 批量计算
        target_matrix = np.vstack(target_features_list)
        similarities = np.dot(target_matrix, query_features)
        similarities = (similarities + 1) / 2  # 映射到0-1
        
        return similarities.tolist()
    
    def classify_image_type(self, image_path: str) -> Dict:
        """
        使用CLIP进行零样本图像分类
        判断图像类型（电路图、力学图、公式、表格等）
        
        Args:
            image_path: 图像路径
            
        Returns:
            分类结果字典
        """
        if not self.is_available():
            return {'type': 'unknown', 'confidence': 0.0}
        
        # 预定义类别
        categories = [
            "a mathematical formula or equation",
            "an electrical circuit diagram", 
            "a physics mechanics diagram with forces",
            "a graph or chart",
            "a table of data",
            "handwritten text",
            "printed text with math symbols",
            "a geometric figure",
        ]
        
        category_names = [
            "formula", "circuit", "mechanics", 
            "graph", "table", "handwritten", 
            "printed_math", "geometry"
        ]
        
        try:
            # 加载图像
            image = Image.open(image_path).convert('RGB')
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)
            
            # 编码文本
            text_inputs = self.tokenizer(categories).to(self.device)
            
            with torch.no_grad():
                image_features = self.model.encode_image(image_input)
                text_features = self.model.encode_text(text_inputs)
                
                # 归一化
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                
                # 计算相似度
                similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
            
            # 获取最高分类
            probs = similarity[0].cpu().numpy()
            max_idx = np.argmax(probs)
            
            return {
                'type': category_names[max_idx],
                'confidence': float(probs[max_idx]),
                'all_scores': {
                    name: float(prob) 
                    for name, prob in zip(category_names, probs)
                }
            }
            
        except Exception as e:
            print(f"CLIP分类失败: {e}")
            return {'type': 'unknown', 'confidence': 0.0}


# 单例实例
_clip_service = None

def get_clip_service() -> CLIPService:
    """获取CLIP服务单例"""
    global _clip_service
    if _clip_service is None:
        _clip_service = CLIPService()
    return _clip_service
