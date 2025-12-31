"""
数据库操作模块
"""
import sqlite3
import json
import numpy as np
from typing import List, Dict, Optional, Tuple
from config import DATABASE_PATH


class QuestionDatabase:
    """题库数据库管理类"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建题目表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT UNIQUE NOT NULL,
                image_path TEXT NOT NULL,
                answer_path TEXT,
                ocr_text TEXT,
                latex_formula TEXT,
                text_embedding BLOB,
                image_embedding BLOB,
                category TEXT,
                difficulty TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_question_id 
            ON questions(question_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_category 
            ON questions(category)
        ''')
        
        conn.commit()
        conn.close()
    
    def insert_question(self, question_data: Dict) -> int:
        """插入题目数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 将 numpy 数组转换为 bytes
        text_embedding = None
        if 'text_embedding' in question_data and question_data['text_embedding'] is not None:
            text_embedding = question_data['text_embedding'].tobytes()
        
        image_embedding = None
        if 'image_embedding' in question_data and question_data['image_embedding'] is not None:
            image_embedding = question_data['image_embedding'].tobytes()
        
        tags_json = json.dumps(question_data.get('tags', []))
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO questions 
                (question_id, image_path, answer_path, ocr_text, latex_formula, 
                 text_embedding, image_embedding, category, difficulty, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                question_data['question_id'],
                question_data['image_path'],
                question_data.get('answer_path'),
                question_data.get('ocr_text'),
                question_data.get('latex_formula'),
                text_embedding,
                image_embedding,
                question_data.get('category'),
                question_data.get('difficulty'),
                tags_json
            ))
            
            question_id = cursor.lastrowid
            conn.commit()
            return question_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_question_by_id(self, question_id: str) -> Optional[Dict]:
        """根据ID获取题目"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM questions WHERE question_id = ?
        ''', (question_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_dict(row)
        return None
    
    def get_all_questions(self) -> List[Dict]:
        """获取所有题目"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM questions')
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def search_by_category(self, category: str) -> List[Dict]:
        """按类别搜索题目"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM questions WHERE category = ?
        ''', (category,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def get_embeddings(self) -> Tuple[List[str], np.ndarray, np.ndarray]:
        """获取所有题目的嵌入向量"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT question_id, text_embedding, image_embedding 
            FROM questions
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        question_ids = []
        text_embeddings = []
        image_embeddings = []
        
        for row in rows:
            question_ids.append(row[0])
            
            if row[1]:
                text_emb = np.frombuffer(row[1], dtype=np.float32)
                text_embeddings.append(text_emb)
            else:
                text_embeddings.append(None)
            
            if row[2]:
                img_emb = np.frombuffer(row[2], dtype=np.float32)
                image_embeddings.append(img_emb)
            else:
                image_embeddings.append(None)
        
        return question_ids, text_embeddings, image_embeddings
    
    def _row_to_dict(self, row: tuple) -> Dict:
        """将数据库行转换为字典"""
        columns = [
            'id', 'question_id', 'image_path', 'answer_path', 'ocr_text',
            'latex_formula', 'text_embedding', 'image_embedding', 
            'category', 'difficulty', 'tags', 'created_at', 'updated_at'
        ]
        
        data = dict(zip(columns, row))
        
        # 解析 JSON 标签
        if data['tags']:
            data['tags'] = json.loads(data['tags'])
        
        # 转换嵌入向量
        if data['text_embedding']:
            data['text_embedding'] = np.frombuffer(data['text_embedding'], dtype=np.float32)
        
        if data['image_embedding']:
            data['image_embedding'] = np.frombuffer(data['image_embedding'], dtype=np.float32)
        
        return data
    
    def delete_question(self, question_id: str) -> bool:
        """删除题目"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM questions WHERE question_id = ?', (question_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def count_questions(self) -> int:
        """统计题目数量"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM questions')
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
