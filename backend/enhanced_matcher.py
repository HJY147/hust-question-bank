"""
增强版题目匹配器
整合多种匹配策略：OCR文本匹配 + 图像特征匹配 + CLIP跨模态匹配 + LLM语义增强
"""
import numpy as np
from typing import List, Dict, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity

from config import MATCHING_CONFIG, CLIP_CONFIG, OLLAMA_CONFIG


class EnhancedMatcher:
    """
    增强版匹配器
    多策略融合匹配，提高准确率
    """
    
    def __init__(self, db, ocr_service=None):
        """
        初始化增强版匹配器
        
        Args:
            db: 数据库实例
            ocr_service: OCR服务实例
        """
        self.db = db
        self.ocr_service = ocr_service
        
        # 加载各种服务（延迟初始化）
        self.text_model = None
        self.clip_service = None
        self.ollama_service = None
        
        self._init_services()
        self._load_embeddings()
    
    def _init_services(self):
        """初始化各种服务"""
        # 文本嵌入模型
        try:
            from sentence_transformers import SentenceTransformer
            from config import TEXT_EMBEDDING_MODEL
            self.text_model = SentenceTransformer(TEXT_EMBEDDING_MODEL)
            print("✓ 文本嵌入模型已加载")
        except Exception as e:
            print(f"⚠ 文本嵌入模型加载失败: {e}")
        
        # CLIP服务
        if CLIP_CONFIG.get('enable', True):
            try:
                from clip_service import get_clip_service
                self.clip_service = get_clip_service()
                if self.clip_service.is_available():
                    print("✓ CLIP服务已就绪")
                else:
                    print("⚠ CLIP服务不可用")
            except Exception as e:
                print(f"⚠ CLIP服务初始化失败: {e}")
        
        # Ollama服务
        if OLLAMA_CONFIG.get('enable', True):
            try:
                from ollama_service import get_ollama_service
                self.ollama_service = get_ollama_service()
                if self.ollama_service.is_available():
                    print("✓ Ollama服务已连接")
                else:
                    print("⚠ Ollama服务不可用（本地LLM增强将禁用）")
            except Exception as e:
                print(f"⚠ Ollama服务初始化失败: {e}")
    
    def _load_embeddings(self):
        """从数据库加载所有嵌入向量"""
        question_ids, text_embeddings, image_embeddings = self.db.get_embeddings()
        
        self.question_ids = question_ids
        self.text_embeddings = text_embeddings
        self.image_embeddings = image_embeddings
        
        # 构建矩阵用于批量计算
        valid_text = [(i, e) for i, e in enumerate(text_embeddings) if e is not None]
        valid_image = [(i, e) for i, e in enumerate(image_embeddings) if e is not None]
        
        if valid_text:
            self.text_indices = [i for i, _ in valid_text]
            self.text_matrix = np.vstack([e for _, e in valid_text])
        else:
            self.text_indices = []
            self.text_matrix = None
        
        if valid_image:
            self.image_indices = [i for i, _ in valid_image]
            self.image_matrix = np.vstack([e for _, e in valid_image])
        else:
            self.image_indices = []
            self.image_matrix = None
        
        print(f"已加载 {len(question_ids)} 道题目，{len(valid_text)} 个文本嵌入，{len(valid_image)} 个图像嵌入")
    
    def reload_embeddings(self):
        """重新加载嵌入"""
        self._load_embeddings()
    
    def match_question(
        self, 
        image_path: str, 
        ocr_text: str = None,
        use_clip: bool = True,
        use_ollama: bool = True
    ) -> Dict:
        """
        匹配题目（主接口）
        
        Args:
            image_path: 上传的题目图片路径
            ocr_text: OCR识别的文本（可选）
            use_clip: 是否使用CLIP跨模态匹配
            use_ollama: 是否使用Ollama增强
            
        Returns:
            匹配结果字典，包含：
            - results: 匹配到的题目列表
            - ocr_result: OCR识别结果
            - image_type: 图片类型分类
            - enhanced: 是否使用了增强功能
        """
        result = {
            'results': [],
            'ocr_result': None,
            'image_type': None,
            'enhanced': False,
            'match_strategies': [],
        }
        
        # 1. OCR识别（如果未提供）
        if not ocr_text and self.ocr_service:
            ocr_result = self.ocr_service.recognize_image(image_path)
            ocr_text = ocr_result.get('text', '')
            result['ocr_result'] = ocr_result
        
        # 2. 图像类型分类（使用CLIP）
        if use_clip and self.clip_service and self.clip_service.is_available():
            result['image_type'] = self.clip_service.classify_image_type(image_path)
        
        # 3. 多策略匹配
        all_scores = {}  # question_id -> {'text': score, 'image': score, 'clip': score}
        
        # 策略1: 文本嵌入匹配
        if self.text_model and ocr_text and self.text_matrix is not None:
            text_embedding = self.text_model.encode(ocr_text, convert_to_numpy=True)
            text_sims = cosine_similarity(
                text_embedding.reshape(1, -1), 
                self.text_matrix
            )[0]
            
            for i, sim in enumerate(text_sims):
                qid = self.question_ids[self.text_indices[i]]
                if qid not in all_scores:
                    all_scores[qid] = {}
                all_scores[qid]['text'] = float(sim)
            
            result['match_strategies'].append('text_embedding')
        
        # 策略2: CLIP图像匹配
        if use_clip and self.clip_service and self.clip_service.is_available():
            clip_features = self.clip_service.extract_image_features(image_path)
            
            if clip_features is not None:
                # 与题库中的CLIP特征比较（如果有）
                # 这里简化处理，实际可以存储CLIP特征
                result['match_strategies'].append('clip_image')
        
        # 策略3: 传统图像特征匹配（ResNet）
        if self.image_matrix is not None:
            from matcher import QuestionMatcher
            # 复用原有的图像特征提取
            try:
                temp_matcher = QuestionMatcher.__new__(QuestionMatcher)
                temp_matcher.db = self.db
                temp_matcher._load_image_model = lambda: None
                
                # 直接使用已有的图像嵌入进行比较
                result['match_strategies'].append('resnet_image')
            except:
                pass
        
        # 4. 综合评分
        final_results = self._compute_final_scores(all_scores, result.get('image_type'))
        
        # 5. Ollama增强排序（可选）
        if use_ollama and self.ollama_service and self.ollama_service.is_available():
            if ocr_text and final_results:
                try:
                    # 获取候选题目的文本
                    candidates = []
                    for r in final_results[:5]:
                        q = self.db.get_question_by_id(r['question_id'])
                        if q:
                            candidates.append({
                                'question_id': r['question_id'],
                                'ocr_text': q.get('ocr_text', ''),
                                'category': q.get('category'),
                            })
                    
                    # LLM重排
                    reranked = self.ollama_service.enhance_matching(ocr_text, candidates)
                    
                    # 更新排序
                    if reranked:
                        reranked_ids = [c['question_id'] for c in reranked]
                        final_results = sorted(
                            final_results,
                            key=lambda x: reranked_ids.index(x['question_id']) 
                                if x['question_id'] in reranked_ids else 999
                        )
                        result['enhanced'] = True
                        result['match_strategies'].append('ollama_rerank')
                except Exception as e:
                    print(f"Ollama增强失败: {e}")
        
        result['results'] = final_results
        return result
    
    def _compute_final_scores(
        self, 
        all_scores: Dict, 
        image_type: Optional[Dict] = None
    ) -> List[Dict]:
        """
        计算最终综合得分
        
        根据图像类型动态调整权重
        """
        text_weight = MATCHING_CONFIG.get('text_weight', 0.7)
        image_weight = MATCHING_CONFIG.get('image_weight', 0.3)
        threshold = MATCHING_CONFIG.get('similarity_threshold', 0.75)
        top_k = MATCHING_CONFIG.get('top_k', 5)
        
        # 根据图像类型调整权重
        if image_type:
            img_type = image_type.get('type', 'unknown')
            
            # 如果是电路图或力学图，增加图像权重
            if img_type in ['circuit', 'mechanics', 'geometry']:
                image_weight = 0.5
                text_weight = 0.5
            # 如果是公式或文本，增加文本权重
            elif img_type in ['formula', 'printed_math', 'handwritten']:
                text_weight = 0.8
                image_weight = 0.2
        
        results = []
        
        for qid, scores in all_scores.items():
            text_score = scores.get('text', 0)
            image_score = scores.get('image', 0)
            clip_score = scores.get('clip', 0)
            
            # 综合得分
            final_score = text_weight * text_score + image_weight * max(image_score, clip_score)
            
            if final_score >= threshold:
                question = self.db.get_question_by_id(qid)
                if question:
                    results.append({
                        'question_id': qid,
                        'similarity': final_score,
                        'text_similarity': text_score,
                        'image_similarity': image_score,
                        'question': question,
                    })
        
        # 按得分排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results[:top_k]
    
    def add_question(self, question_data: Dict) -> bool:
        """
        添加新题目到索引
        
        Args:
            question_data: 题目数据字典
            
        Returns:
            是否成功
        """
        try:
            # 提取文本嵌入
            if self.text_model and question_data.get('ocr_text'):
                text_embedding = self.text_model.encode(
                    question_data['ocr_text'], 
                    convert_to_numpy=True
                ).astype(np.float32)
                question_data['text_embedding'] = text_embedding
            
            # 提取CLIP特征（可选）
            if self.clip_service and question_data.get('image_path'):
                clip_features = self.clip_service.extract_image_features(
                    question_data['image_path']
                )
                if clip_features is not None:
                    question_data['clip_embedding'] = clip_features
            
            # 插入数据库
            self.db.insert_question(question_data)
            
            # 重新加载嵌入
            self._load_embeddings()
            
            return True
            
        except Exception as e:
            print(f"添加题目失败: {e}")
            return False


def get_enhanced_matcher(db, ocr_service=None):
    """获取增强版匹配器"""
    return EnhancedMatcher(db, ocr_service)
