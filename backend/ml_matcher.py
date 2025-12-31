"""
机器学习增强匹配模块
使用机器学习优化题目匹配准确度
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pickle
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import json

from .config import config


class MLMatcher:
    """机器学习匹配增强器"""
    
    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = model_dir or config.ML_MODEL_DIR
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.classifier = None
        self.scaler = StandardScaler()
        self.feature_weights = {
            'text_similarity': config.ML_TEXT_WEIGHT,
            'image_similarity': config.ML_IMAGE_WEIGHT,
            'category_match': 0.2,
            'length_ratio': 0.1
        }
        
        # 加载已训练模型
        self.load_model()
    
    def extract_features(self, 
                        query_embedding: np.ndarray,
                        candidate_embedding: np.ndarray,
                        query_category: str,
                        candidate_category: str,
                        query_length: int,
                        candidate_length: int) -> np.ndarray:
        """
        提取特征向量
        
        Args:
            query_embedding: 查询题目的嵌入向量
            candidate_embedding: 候选题目的嵌入向量
            query_category: 查询题目类别
            candidate_category: 候选题目类别
            query_length: 查询文本长度
            candidate_length: 候选文本长度
            
        Returns:
            特征向量
        """
        features = []
        
        # 1. 余弦相似度
        cosine_sim = np.dot(query_embedding, candidate_embedding) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(candidate_embedding)
        )
        features.append(cosine_sim)
        
        # 2. 欧氏距离（归一化）
        euclidean_dist = np.linalg.norm(query_embedding - candidate_embedding)
        features.append(1 / (1 + euclidean_dist))  # 转换为相似度
        
        # 3. 类别匹配（one-hot）
        category_match = 1.0 if query_category == candidate_category else 0.0
        features.append(category_match)
        
        # 4. 长度比率
        length_ratio = min(query_length, candidate_length) / max(query_length, candidate_length)
        features.append(length_ratio)
        
        # 5. 向量的统计特征
        features.append(np.mean(query_embedding))
        features.append(np.std(query_embedding))
        features.append(np.mean(candidate_embedding))
        features.append(np.std(candidate_embedding))
        
        # 6. 向量差异
        diff = query_embedding - candidate_embedding
        features.append(np.mean(np.abs(diff)))
        features.append(np.max(np.abs(diff)))
        
        return np.array(features)
    
    def train(self, 
             training_data: List[Dict[str, Any]], 
             save_model: bool = True) -> Dict[str, float]:
        """
        训练匹配模型
        
        Args:
            training_data: 训练数据列表，每项包含:
                {
                    'query_embedding': np.ndarray,
                    'candidate_embedding': np.ndarray,
                    'query_category': str,
                    'candidate_category': str,
                    'query_length': int,
                    'candidate_length': int,
                    'is_match': bool  # 标签：是否匹配
                }
            save_model: 是否保存模型
            
        Returns:
            训练指标字典
        """
        if len(training_data) < config.ML_MIN_SAMPLES:
            return {
                'error': f'训练样本不足，需要至少 {config.ML_MIN_SAMPLES} 个样本',
                'samples': len(training_data)
            }
        
        # 提取特征和标签
        X = []
        y = []
        
        for sample in training_data:
            features = self.extract_features(
                sample['query_embedding'],
                sample['candidate_embedding'],
                sample['query_category'],
                sample['candidate_category'],
                sample['query_length'],
                sample['candidate_length']
            )
            X.append(features)
            y.append(1 if sample['is_match'] else 0)
        
        X = np.array(X)
        y = np.array(y)
        
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # 标准化特征
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 训练梯度提升分类器
        self.classifier = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        self.classifier.fit(X_train_scaled, y_train)
        
        # 评估模型
        train_score = self.classifier.score(X_train_scaled, y_train)
        test_score = self.classifier.score(X_test_scaled, y_test)
        
        # 特征重要性
        feature_importance = self.classifier.feature_importances_
        
        metrics = {
            'train_accuracy': float(train_score),
            'test_accuracy': float(test_score),
            'samples': len(training_data),
            'feature_importance': feature_importance.tolist()
        }
        
        # 保存模型
        if save_model:
            self.save_model(metrics)
        
        print(f"✅ 模型训练完成:")
        print(f"  训练准确率: {train_score:.4f}")
        print(f"  测试准确率: {test_score:.4f}")
        
        return metrics
    
    def predict_similarity(self,
                          query_embedding: np.ndarray,
                          candidate_embedding: np.ndarray,
                          query_category: str,
                          candidate_category: str,
                          query_length: int,
                          candidate_length: int) -> float:
        """
        预测匹配相似度
        
        Returns:
            相似度分数 (0-1)
        """
        if self.classifier is None:
            # 如果模型未训练，使用简单余弦相似度
            return float(np.dot(query_embedding, candidate_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(candidate_embedding)
            ))
        
        # 提取特征
        features = self.extract_features(
            query_embedding,
            candidate_embedding,
            query_category,
            candidate_category,
            query_length,
            candidate_length
        )
        
        # 标准化
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        
        # 预测概率（类别1的概率即为相似度）
        similarity = self.classifier.predict_proba(features_scaled)[0][1]
        
        return float(similarity)
    
    def save_model(self, metrics: Optional[Dict] = None):
        """保存模型到磁盘"""
        model_path = self.model_dir / 'ml_matcher.pkl'
        scaler_path = self.model_dir / 'scaler.pkl'
        metrics_path = self.model_dir / 'metrics.json'
        
        with open(model_path, 'wb') as f:
            pickle.dump(self.classifier, f)
        
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        if metrics:
            with open(metrics_path, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        print(f"💾 模型已保存: {model_path}")
    
    def load_model(self) -> bool:
        """从磁盘加载模型"""
        model_path = self.model_dir / 'ml_matcher.pkl'
        scaler_path = self.model_dir / 'scaler.pkl'
        
        if not model_path.exists() or not scaler_path.exists():
            print("ℹ️  未找到已训练的ML模型，将使用基础相似度计算")
            return False
        
        try:
            with open(model_path, 'rb') as f:
                self.classifier = pickle.load(f)
            
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            
            print(f"✅ ML模型已加载: {model_path}")
            return True
        except Exception as e:
            print(f"❌ 加载模型失败: {e}")
            return False


def generate_training_data_from_db(db_path: str, 
                                   num_positive: int = 100,
                                   num_negative: int = 300) -> List[Dict]:
    """
    从数据库生成训练数据
    
    Args:
        db_path: 数据库路径
        num_positive: 正样本数量（相同题目）
        num_negative: 负样本数量（不同题目）
        
    Returns:
        训练数据列表
    """
    import sqlite3
    
    training_data = []
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取所有题目
    cursor.execute("""
        SELECT question_id, category, question_text, text_embedding
        FROM questions
    """)
    
    questions = []
    for row in cursor.fetchall():
        q_id, category, text, embedding_blob = row
        embedding = np.frombuffer(embedding_blob, dtype=np.float32)
        questions.append({
            'id': q_id,
            'category': category,
            'text': text,
            'embedding': embedding,
            'length': len(text)
        })
    
    conn.close()
    
    # 生成正样本（同一题目的变体，这里用题目自身作为正样本）
    for i, q in enumerate(questions[:num_positive]):
        training_data.append({
            'query_embedding': q['embedding'],
            'candidate_embedding': q['embedding'],
            'query_category': q['category'],
            'candidate_category': q['category'],
            'query_length': q['length'],
            'candidate_length': q['length'],
            'is_match': True
        })
    
    # 生成负样本（不同类别的题目对）
    import random
    for _ in range(num_negative):
        q1, q2 = random.sample(questions, 2)
        # 确保类别不同
        if q1['category'] == q2['category']:
            continue
        
        training_data.append({
            'query_embedding': q1['embedding'],
            'candidate_embedding': q2['embedding'],
            'query_category': q1['category'],
            'candidate_category': q2['category'],
            'query_length': q1['length'],
            'candidate_length': q2['length'],
            'is_match': False
        })
    
    print(f"📊 生成训练数据: {len(training_data)} 个样本")
    return training_data


if __name__ == '__main__':
    # 测试ML匹配器
    from backend.config import Config
    
    Config.print_status()
    
    # 训练模型示例
    db_path = Config.DB_PATH
    if db_path.exists():
        print("\n开始训练ML模型...")
        training_data = generate_training_data_from_db(str(db_path))
        
        matcher = MLMatcher()
        metrics = matcher.train(training_data)
        
        print("\n训练完成！")
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
