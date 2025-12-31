"""
Ollama 集成服务
用于增强题目理解和语义匹配
支持本地部署的LLM模型
"""
import requests
import json
from typing import Dict, List, Optional
from config import OLLAMA_CONFIG


class OllamaService:
    """Ollama服务封装类"""
    
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or OLLAMA_CONFIG.get('base_url', 'http://localhost:11434')
        self.model = model or OLLAMA_CONFIG.get('model', 'qwen2:7b')
        self.timeout = OLLAMA_CONFIG.get('timeout', 60)
        self._available = None
    
    def is_available(self) -> bool:
        """检查Ollama服务是否可用"""
        if self._available is not None:
            return self._available
        
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            self._available = response.status_code == 200
        except:
            self._available = False
        
        return self._available
    
    def list_models(self) -> List[str]:
        """获取可用的模型列表"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
        except:
            pass
        return []
    
    def generate(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """
        生成文本响应
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示（可选）
            
        Returns:
            生成的文本，失败返回None
        """
        if not self.is_available():
            return None
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 500,
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('message', {}).get('content', '')
            
        except Exception as e:
            print(f"Ollama生成失败: {e}")
        
        return None
    
    def extract_question_keywords(self, ocr_text: str) -> List[str]:
        """
        从OCR文本中提取关键词
        用于增强题目匹配
        
        Args:
            ocr_text: OCR识别的文本
            
        Returns:
            关键词列表
        """
        system_prompt = """你是一个专业的数学/物理题目分析助手。
请从给定的题目文本中提取关键信息，包括：
1. 学科领域（如：微积分、复变函数、大学物理、电路理论等）
2. 知识点（如：积分、极限、麦克斯韦方程等）
3. 关键数学符号或公式特征

只返回关键词，用逗号分隔，不要其他解释。"""
        
        prompt = f"请分析以下题目文本并提取关键词：\n\n{ocr_text}"
        
        result = self.generate(prompt, system_prompt)
        
        if result:
            # 解析关键词
            keywords = [kw.strip() for kw in result.split(',') if kw.strip()]
            return keywords
        
        return []
    
    def classify_question(self, ocr_text: str) -> Dict:
        """
        对题目进行分类
        
        Args:
            ocr_text: OCR识别的文本
            
        Returns:
            分类结果字典，包含科目、知识点、难度等
        """
        system_prompt = """你是一个专业的题目分类助手。
请分析给定的题目，返回JSON格式的分类结果，包含以下字段：
- subject: 科目（calculus/complex_analysis/physics/circuit/mechanics/other）
- topic: 具体知识点
- difficulty: 难度（easy/medium/hard）
- has_formula: 是否包含公式（true/false）
- has_figure: 是否需要图形（true/false）

只返回JSON，不要其他解释。"""
        
        prompt = f"请分析并分类以下题目：\n\n{ocr_text}"
        
        result = self.generate(prompt, system_prompt)
        
        if result:
            try:
                # 尝试解析JSON
                # 处理可能的markdown代码块
                if '```' in result:
                    result = result.split('```')[1]
                    if result.startswith('json'):
                        result = result[4:]
                
                return json.loads(result.strip())
            except:
                pass
        
        return {
            'subject': 'other',
            'topic': 'unknown',
            'difficulty': 'medium',
            'has_formula': False,
            'has_figure': False
        }
    
    def generate_question_description(self, ocr_text: str) -> str:
        """
        生成题目的规范化描述
        用于更好的语义匹配
        
        Args:
            ocr_text: OCR识别的原始文本
            
        Returns:
            规范化的题目描述
        """
        system_prompt = """你是一个专业的题目整理助手。
请将OCR识别的题目文本整理成规范的格式：
1. 修正可能的OCR识别错误
2. 整理公式格式
3. 补充可能缺失的上下文
4. 保持题目的核心内容不变

直接返回整理后的题目文本，不要其他解释。"""
        
        prompt = f"请整理以下OCR识别的题目文本：\n\n{ocr_text}"
        
        result = self.generate(prompt, system_prompt)
        
        return result if result else ocr_text
    
    def enhance_matching(self, query_text: str, candidates: List[Dict]) -> List[Dict]:
        """
        使用LLM增强匹配结果排序
        
        Args:
            query_text: 查询题目文本
            candidates: 候选题目列表
            
        Returns:
            重新排序后的候选列表
        """
        if not candidates or not self.is_available():
            return candidates
        
        # 只对前几个候选进行LLM重排
        top_candidates = candidates[:5]
        
        system_prompt = """你是一个题目匹配专家。
给定一个查询题目和几个候选题目，请判断哪个候选题目与查询题目最相似。
考虑：
1. 题目类型是否相同
2. 涉及的知识点是否相同
3. 题目结构是否相似
4. 数值或参数是否可能只是变体

返回JSON格式：{"ranking": [索引1, 索引2, ...], "confidence": 0.0-1.0}"""
        
        # 构建候选描述
        candidates_text = ""
        for i, c in enumerate(top_candidates):
            candidates_text += f"\n候选{i}: {c.get('ocr_text', '')[:200]}"
        
        prompt = f"查询题目：{query_text[:300]}\n\n候选题目：{candidates_text}\n\n请分析并排序。"
        
        result = self.generate(prompt, system_prompt)
        
        if result:
            try:
                if '```' in result:
                    result = result.split('```')[1]
                    if result.startswith('json'):
                        result = result[4:]
                
                ranking_data = json.loads(result.strip())
                ranking = ranking_data.get('ranking', list(range(len(top_candidates))))
                
                # 按新排序重组
                reranked = []
                for idx in ranking:
                    if 0 <= idx < len(top_candidates):
                        reranked.append(top_candidates[idx])
                
                # 添加未被重排的候选
                remaining = candidates[5:]
                return reranked + remaining
                
            except:
                pass
        
        return candidates


# 单例实例
_ollama_service = None

def get_ollama_service() -> OllamaService:
    """获取Ollama服务单例"""
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service
