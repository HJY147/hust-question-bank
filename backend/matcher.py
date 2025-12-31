"""
题目匹配服务
使用多种策略匹配题库中的题目
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity
import cv2

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("Warning: sentence-transformers not installed. 文本匹配功能将受限")

try:
    from torchvision import models, transforms
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("Warning: PyTorch not installed. 图像匹配功能将受限")

from config import MATCHING_CONFIG, TEXT_EMBEDDING_MODEL, IMAGE_FEATURE_MODEL
from database import QuestionDatabase


class QuestionMatcher:
    """题目匹配器"""
    
    def __init__(self, db: QuestionDatabase):
        self.db = db
        
        # 初始化文本嵌入模型
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.text_model = SentenceTransformer(TEXT_EMBEDDING_MODEL)
            except:
                print("Warning: 文本嵌入模型加载失败")
                self.text_model = None
        else:
            self.text_model = None
        
        # 初始化图像特征提取模型
        if TORCH_AVAILABLE:
            try:
                self.image_model = self._load_image_model()
                self.image_transform = self._get_image_transform()
            except:
                print("Warning: 图像模型加载失败")
                self.image_model = None
                self.image_transform = None
        else:
            self.image_model = None
            self.image_transform = None
        
        # 加载题库嵌入
        self.load_question_embeddings()
    
    def _load_image_model(self):
        """加载预训练的图像特征提取模型"""
        if IMAGE_FEATURE_MODEL == 'resnet50':
            model = models.resnet50(pretrained=True)
            # 移除最后的分类层，只保留特征提取
            model = torch.nn.Sequential(*list(model.children())[:-1])
        elif IMAGE_FEATURE_MODEL == 'vgg16':
            model = models.vgg16(pretrained=True)
            model = model.features
        else:
            model = models.resnet50(pretrained=True)
            model = torch.nn.Sequential(*list(model.children())[:-1])
        
        model.eval()
        return model
    
    def _get_image_transform(self):
        """获取图像预处理转换"""
        return transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225]),
        ])
    
    def load_question_embeddings(self):
        """从数据库加载所有题目的嵌入向量"""
        question_ids, text_embeddings, image_embeddings = self.db.get_embeddings()
        
        self.question_ids = question_ids
        self.text_embeddings = [e for e in text_embeddings if e is not None]
        self.image_embeddings = [e for e in image_embeddings if e is not None]
        
        # 转换为numpy数组用于批量计算
        if self.text_embeddings:
            self.text_embeddings_matrix = np.vstack(self.text_embeddings)
        else:
            self.text_embeddings_matrix = None
        
        if self.image_embeddings:
            self.image_embeddings_matrix = np.vstack(self.image_embeddings)
        else:
            self.image_embeddings_matrix = None
    
    def extract_text_embedding(self, text: str) -> Optional[np.ndarray]:
        """提取文本嵌入向量"""
        if not self.text_model or not text.strip():
            return None
        
        try:
            embedding = self.text_model.encode(text, convert_to_numpy=True)
            return embedding.astype(np.float32)
        except Exception as e:
            print(f"文本嵌入提取失败: {e}")
            return None
    
    def extract_image_embedding(self, image_path: str) -> Optional[np.ndarray]:
        """提取图像特征向量"""
        if not self.image_model or not self.image_transform:
            return None
        
        try:
            # 读取图像
            img = cv2.imread(image_path)
            if img is None:
                return None
            
            # 转换颜色空间
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # 应用转换
            img_tensor = self.image_transform(img_rgb).unsqueeze(0)
            
            # 提取特征
            with torch.no_grad():
                features = self.image_model(img_tensor)
            
            # 展平并转换为numpy
            features = features.squeeze().numpy().astype(np.float32)
            
            # 归一化
            features = features / (np.linalg.norm(features) + 1e-8)
            
            return features
        except Exception as e:
            print(f"图像特征提取失败: {e}")
            return None
    
    def find_similar_questions(
        self, 
        text_embedding: Optional[np.ndarray] = None,
        image_embedding: Optional[np.ndarray] = None,
        top_k: int = None
    ) -> List[Dict]:
        """
        查找相似题目
        
        Args:
            text_embedding: 文本嵌入向量
            image_embedding: 图像嵌入向量
            top_k: 返回前K个结果
            
        Returns:
            匹配结果列表，包含题目ID、相似度等信息
        """
        if top_k is None:
            top_k = MATCHING_CONFIG['top_k']
        
        text_weight = MATCHING_CONFIG['text_weight']
        image_weight = MATCHING_CONFIG['image_weight']
        threshold = MATCHING_CONFIG['similarity_threshold']
        
        # 计算文本相似度
        text_similarities = None
        if text_embedding is not None and self.text_embeddings_matrix is not None:
            text_similarities = cosine_similarity(
                text_embedding.reshape(1, -1), 
                self.text_embeddings_matrix
            )[0]
        
        # 计算图像相似度
        image_similarities = None
        if image_embedding is not None and self.image_embeddings_matrix is not None:
            image_similarities = cosine_similarity(
                image_embedding.reshape(1, -1),
                self.image_embeddings_matrix
            )[0]
        
        # 综合相似度
        if text_similarities is not None and image_similarities is not None:
            # 确保两个数组长度一致
            min_len = min(len(text_similarities), len(image_similarities))
            combined_similarities = (
                text_weight * text_similarities[:min_len] + 
                image_weight * image_similarities[:min_len]
            )
        elif text_similarities is not None:
            combined_similarities = text_similarities
        elif image_similarities is not None:
            combined_similarities = image_similarities
        else:
            return []
        
        # 获取Top-K结果
        top_indices = np.argsort(combined_similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            similarity = float(combined_similarities[idx])
            
            if similarity < threshold:
                continue
            
            question_id = self.question_ids[idx]
            question = self.db.get_question_by_id(question_id)
            
            if question:
                results.append({
                    'question_id': question_id,
                    'similarity': similarity,
                    'question': question,
                    'text_similarity': float(text_similarities[idx]) if text_similarities is not None else None,
                    'image_similarity': float(image_similarities[idx]) if image_similarities is not None else None,
                })
        
        return results
    
    def match_question(
        self, 
        image_path: str, 
        ocr_text: str = None,
        use_ml: bool = True
    ) -> List[Dict]:
        """
        匹配题目（主接口，支持ML增强）
        
        Args:
            image_path: 上传的题目图片路径
            ocr_text: OCR识别的文本（可选，如果不提供会自动识别）
            use_ml: 是否使用机器学习增强匹配
            
        Returns:
            匹配结果列表
        """
        from .config import config
        
        # 提取特征
        text_embedding = None
        if ocr_text:
            text_embedding = self.extract_text_embedding(ocr_text)
        
        image_embedding = self.extract_image_embedding(image_path)
        
        # 查找相似题目
        results = self.find_similar_questions(
            text_embedding=text_embedding,
            image_embedding=image_embedding
        )
        
        # ML增强：重新计算相似度
        if use_ml and config.ENABLE_ML_MATCHING and text_embedding is not None:
            try:
                from .ml_matcher import MLMatcher
                ml_matcher = MLMatcher()
                
                if ml_matcher.classifier is not None:
                    # 使用ML模型重新评分
                    for result in results:
                        q = result['question']
                        # 获取候选题目的embedding
                        candidate_embedding = self.text_embeddings[self.question_ids.index(q['question_id'])]
                        
                        # ML预测相似度
                        ml_similarity = ml_matcher.predict_similarity(
                            text_embedding,
                            candidate_embedding,
                            'unknown',  # 查询类别
                            q.get('category', 'other'),
                            len(ocr_text) if ocr_text else 0,
                            len(q.get('ocr_text', ''))
                        )
                        
                        # 更新相似度（加权平均）
                        result['ml_similarity'] = ml_similarity
                        result['similarity'] = 0.6 * result['similarity'] + 0.4 * ml_similarity
                    
                    # 重新排序
                    results.sort(key=lambda x: x['similarity'], reverse=True)
            except Exception as e:
                print(f"⚠️  ML增强失败: {e}")
        
        return results
    
    def add_question_to_index(self, question_data: Dict):
        """
        添加题目到索引（用于实时更新）
        
        Args:
            question_data: 题目数据
        """
        # 重新加载嵌入
        self.load_question_embeddings()


class SimpleTextMatcher:
    """
    简单文本匹配器（当高级模型不可用时使用）
    基于编辑距离和关键词匹配
    """
    
    def __init__(self, db: QuestionDatabase):
        self.db = db
    
    def match_question(self, ocr_text: str) -> List[Dict]:
        """使用简单的文本相似度匹配"""
        all_questions = self.db.get_all_questions()
        
        results = []
        for question in all_questions:
            if not question.get('ocr_text'):
                continue
            
            # 简单的相似度计算（基于共同词汇）
            similarity = self._simple_text_similarity(
                ocr_text, 
                question['ocr_text']
            )
            
            if similarity > MATCHING_CONFIG['similarity_threshold']:
                results.append({
                    'question_id': question['question_id'],
                    'similarity': similarity,
                    'question': question,
                })
        
        # 按相似度排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results[:MATCHING_CONFIG['top_k']]
    
    def _simple_text_similarity(self, text1: str, text2: str) -> float:
        """简单的文本相似度计算"""
        # 分词（简单按空格和字符分割）
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Jaccard 相似度
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)


def get_matcher(db: QuestionDatabase):
    """获取匹配器实例"""
    if SENTENCE_TRANSFORMERS_AVAILABLE or TORCH_AVAILABLE:
        return QuestionMatcher(db)
    else:
        return SimpleTextMatcher(db)
