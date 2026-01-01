"""
数据库操作模块 - 增强版
支持题目、答案、搜索历史、收藏、纠错等功能
"""
import sqlite3
import json
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# 尝试导入numpy，如果不存在则设为None
try:
    import numpy as np
except ImportError:
    np = None

# 数据库路径
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '../data/database.db')


def get_db_path():
    return DATABASE_PATH


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
    
    def get_embeddings(self) -> Tuple[List[str], list, list]:
        """获取所有题目的嵌入向量"""
        if np is None:
            return [], [], []
        
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
            
            if row[1] and np is not None:
                text_emb = np.frombuffer(row[1], dtype=np.float32)
                text_embeddings.append(text_emb)
            else:
                text_embeddings.append(None)
            
            if row[2] and np is not None:
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
        
        # 转换嵌入向量（仅当numpy可用时）
        if np is not None:
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


# ==================== 扩展功能：搜索历史、收藏、纠错 ====================

class ExtendedDatabase:
    """扩展数据库功能"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_extended_tables()
    
    def init_extended_tables(self):
        """初始化扩展表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 搜索历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_ip TEXT,
                search_image TEXT,
                ocr_text TEXT,
                results TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 收藏表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_ip TEXT NOT NULL,
                question_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_ip, question_id)
            )
        ''')
        
        # 纠错反馈表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL,
                content TEXT NOT NULL,
                user_ip TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_user ON search_history(user_ip)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_ip)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_status ON error_reports(status)')
        
        conn.commit()
        conn.close()
    
    # ---- 搜索历史 ----
    def add_search_history(self, user_ip: str, search_image: str, ocr_text: str, results: list) -> int:
        """添加搜索历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        results_json = json.dumps(results, ensure_ascii=False) if results else '[]'
        cursor.execute('''
            INSERT INTO search_history (user_ip, search_image, ocr_text, results)
            VALUES (?, ?, ?, ?)
        ''', (user_ip, search_image, ocr_text, results_json))
        
        history_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return history_id
    
    def get_search_history(self, user_ip: str, limit: int = 20) -> List[Dict]:
        """获取用户搜索历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, user_ip, search_image, ocr_text, results, created_at
            FROM search_history 
            WHERE user_ip = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_ip, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            item = {
                'id': row[0],
                'user_ip': row[1],
                'search_image': row[2],
                'ocr_text': row[3],
                'results': json.loads(row[4]) if row[4] else [],
                'created_at': row[5]
            }
            results.append(item)
        return results
    
    def clear_search_history(self, user_ip: str) -> int:
        """清除用户搜索历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM search_history WHERE user_ip = ?', (user_ip,))
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count
    
    # ---- 收藏功能 ----
    def add_favorite(self, user_ip: str, question_id: str) -> bool:
        """添加收藏"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO favorites (user_ip, question_id)
                VALUES (?, ?)
            ''', (user_ip, question_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # 已收藏
        finally:
            conn.close()
    
    def remove_favorite(self, user_ip: str, question_id: str) -> bool:
        """取消收藏"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM favorites 
            WHERE user_ip = ? AND question_id = ?
        ''', (user_ip, question_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def get_favorites(self, user_ip: str, page: int = 1, per_page: int = 20) -> List[Dict]:
        """获取用户收藏列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT id, user_ip, question_id, created_at
            FROM favorites
            WHERE user_ip = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (user_ip, per_page, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{'id': r[0], 'user_ip': r[1], 'question_id': r[2], 'created_at': r[3]} for r in rows]
    
    def is_favorited(self, user_ip: str, question_id: str) -> bool:
        """检查是否已收藏"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 1 FROM favorites 
            WHERE user_ip = ? AND question_id = ?
        ''', (user_ip, question_id))
        
        result = cursor.fetchone() is not None
        conn.close()
        return result
    
    def get_favorite_count(self, user_ip: str) -> int:
        """获取收藏数量"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM favorites WHERE user_ip = ?', (user_ip,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    # ---- 纠错反馈 ----
    def add_error_report(self, question_id: str, content: str, user_ip: str = '') -> int:
        """添加纠错反馈"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO error_reports (question_id, content, user_ip)
            VALUES (?, ?, ?)
        ''', (question_id, content, user_ip))
        
        report_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return report_id
    
    def get_error_reports(self, status: str = None, limit: int = 50) -> List[Dict]:
        """获取纠错反馈列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status:
            cursor.execute('''
                SELECT id, question_id, content, user_ip, status, created_at
                FROM error_reports 
                WHERE status = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (status, limit))
        else:
            cursor.execute('''
                SELECT id, question_id, content, user_ip, status, created_at
                FROM error_reports 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{'id': r[0], 'question_id': r[1], 'content': r[2], 
                'user_ip': r[3], 'status': r[4], 'created_at': r[5]} for r in rows]
    
    def update_report_status(self, report_id: int, status: str) -> bool:
        """更新纠错状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE error_reports SET status = ? WHERE id = ?', (status, report_id))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    # ---- 统计信息 ----
    def get_statistics(self) -> Dict:
        """获取系统统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # 题目数量
        try:
            cursor.execute('SELECT COUNT(*) FROM questions')
            stats['total_questions'] = cursor.fetchone()[0]
        except:
            stats['total_questions'] = 0
        
        # 今日搜索量
        try:
            cursor.execute('''
                SELECT COUNT(*) FROM search_history 
                WHERE DATE(created_at) = DATE('now')
            ''')
            stats['today_searches'] = cursor.fetchone()[0]
        except:
            stats['today_searches'] = 0
        
        # 总搜索量
        try:
            cursor.execute('SELECT COUNT(*) FROM search_history')
            stats['total_searches'] = cursor.fetchone()[0]
        except:
            stats['total_searches'] = 0
        
        # 待处理纠错
        try:
            cursor.execute("SELECT COUNT(*) FROM error_reports WHERE status = 'pending'")
            stats['pending_reports'] = cursor.fetchone()[0]
        except:
            stats['pending_reports'] = 0
        
        conn.close()
        return stats


# 全局实例
_question_db = None
_extended_db = None


def get_question_db() -> QuestionDatabase:
    """获取题目数据库实例"""
    global _question_db
    if _question_db is None:
        _question_db = QuestionDatabase()
    return _question_db


def get_extended_db() -> ExtendedDatabase:
    """获取扩展数据库实例"""
    global _extended_db
    if _extended_db is None:
        _extended_db = ExtendedDatabase()
    return _extended_db


# 便捷函数
def init_all_tables():
    """初始化所有数据库表"""
    get_question_db()
    get_extended_db()
    print(f"[Database] All tables initialized at {DATABASE_PATH}")


if __name__ == '__main__':
    init_all_tables()
    stats = get_extended_db().get_statistics()
    print(f"Statistics: {stats}")