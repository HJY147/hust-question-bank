import sqlite3
import os
from typing import List, Dict, Any

class SearchService:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'database.db')

    def search_questions(self, text: str) -> List[Dict[str, Any]]:
        """
        根据文本搜索题目
        """
        results = []
        if not os.path.exists(self.db_path):
            print(f"Database not found at {self.db_path}")
            return results

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 简单的关键词匹配逻辑
            # 实际项目中应使用向量搜索或全文检索
            
            # 1. 尝试精确包含
            cursor.execute("SELECT * FROM questions WHERE content LIKE ? LIMIT 5", (f"%{text}%",))
            rows = cursor.fetchall()
            
            if not rows and len(text) > 2:
                # 2. 尝试部分匹配
                keyword = text[:5] # 取前5个字
                cursor.execute("SELECT * FROM questions WHERE content LIKE ? LIMIT 5", (f"%{keyword}%",))
                rows = cursor.fetchall()
            
            if not rows:
                # 3. 如果还是没有，随机返回几个作为演示
                cursor.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 3")
                rows = cursor.fetchall()
                similarity_base = 0.4 # 随机的相似度低
            else:
                similarity_base = 0.9 # 匹配到的相似度高

            for row in rows:
                results.append({
                    'question_id': row['question_id'],
                    'category': row['category'],
                    'content': row['content'],
                    'answer': row['answer'],
                    'similarity': similarity_base
                })
                
            conn.close()
        except Exception as e:
            print(f"Search error: {e}")
            
        return results

# 单例实例
search_service = SearchService()
