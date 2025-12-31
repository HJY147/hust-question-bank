"""
AI服务模块
集成DeepSeek和豆包API，提供智能解题和图像识别
"""
import base64
import json
import requests
from typing import Optional, Dict, Any
from pathlib import Path
import time

from config import config

# 优化：创建全局会话，复用连接，减少建立连接的时间开销
_http_session = None

def get_http_session():
    """获取或创建HTTP会话（带连接池）"""
    global _http_session
    if _http_session is None:
        _http_session = requests.Session()
        # 配置连接池
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,  # 连接池大小
            pool_maxsize=20,      # 最大连接数
            max_retries=1,        # 重试次数
            pool_block=False      # 不阻塞
        )
        _http_session.mount('http://', adapter)
        _http_session.mount('https://', adapter)
    return _http_session


class DeepSeekSolver:
    """DeepSeek AI解题服务"""
    
    def __init__(self):
        self.api_key = config.DEEPSEEK_API_KEY
        self.base_url = config.DEEPSEEK_BASE_URL
        self.timeout = config.AI_TIMEOUT
        
    def solve_question(self, question_text: str, category: Optional[str] = None) -> Dict[str, Any]:
        """
        使用DeepSeek解答题目
        
        Args:
            question_text: 题目文本
            category: 题目类别（可选，用于优化提示词）
            
        Returns:
            {
                'success': bool,
                'answer': str,  # 解答内容
                'steps': list,  # 解题步骤
                'confidence': float,  # 置信度
                'model': str,  # 使用的模型
                'error': str  # 错误信息（如果失败）
            }
        """
        if not self.api_key or self.api_key == 'your_deepseek_api_key_here':
            return {
                'success': False,
                'error': 'DeepSeek API密钥未配置'
            }
        
        # 构建提示词
        category_hints = {
            'calculus': '微积分',
            'physics': '大学物理',
            'circuit': '电路理论',
            'complex_analysis': '复变函数',
            'mechanics': '理论力学',
            'linear_algebra': '线性代数',
            'probability': '概率论',
            'other': '数学或物理'
        }
        
        category_name = category_hints.get(category, '数学或物理')
        
        # 优化：精简提示词，减少token消耗，加快生成速度
        system_prompt = f"""你是{category_name}解题助手。要求：
1. 列出解题步骤（用序号）
2. 给出最终答案
3. 数学公式用LaTeX：行内用$...$ ，独立用$$...$$
4. 中文解答，简洁准确"""

        user_prompt = f"{category_name}题目：\n{question_text}\n\n请解答。"

        try:
            # 调用DeepSeek API
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # 优化：使用配置中的优化参数，进一步提升响应速度
            data = {
                'model': 'deepseek-chat',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': config.AI_TEMPERATURE,  # 优化：使用更低的temperature
                'max_tokens': config.MAX_TOKENS,  # 优化：减少token数量
                'stream': False,  # 非流式响应
                'top_p': 0.9  # 优化：添加top_p采样，提高生成效率
            }
            
            # 优化：使用会话复用连接，减少建立连接的时间
            session = get_http_session()
            response = session.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                answer_text = result['choices'][0]['message']['content']
                
                # 解析步骤（简单分段）
                steps = []
                for line in answer_text.split('\n'):
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith('步骤')):
                        steps.append(line)
                
                return {
                    'success': True,
                    'answer': answer_text,
                    'steps': steps if steps else [answer_text],
                    'confidence': 0.85,  # DeepSeek通常较准确
                    'model': 'deepseek-chat',
                    'source': 'AI实时解答'
                }
            else:
                return {
                    'success': False,
                    'error': f'API调用失败: {response.status_code} - {response.text}'
                }
                
        except requests.Timeout:
            return {
                'success': False,
                'error': f'请求超时（超过{self.timeout}秒）'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'DeepSeek调用异常: {str(e)}'
            }


class DoubaoVision:
    """豆包图像识别服务 - 使用官方SDK"""
    
    def __init__(self):
        self.api_key = config.DOUBAO_API_KEY
        self.endpoint_id = config.DOUBAO_ENDPOINT_ID
        self.region = config.DOUBAO_REGION
        self.timeout = config.AI_TIMEOUT
        
        # 初始化火山引擎客户端
        try:
            from volcenginesdkarkruntime import Ark
            self.client = Ark(api_key=self.api_key)
            print(f"[SDK] 豆包SDK初始化成功")
        except ImportError as e:
            print(f"[Error] 豆包SDK导入失败: {e}")
            self.client = None
        
    def extract_question_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        使用豆包识别图片中的题目文本
        
        Args:
            image_path: 图片路径
            
        Returns:
            {
                'success': bool,
                'text': str,  # 识别的文本
                'confidence': float,  # 置信度
                'structured_info': dict,  # 结构化信息
                'error': str  # 错误信息
            }
        """
        if not self.api_key or self.api_key == 'your_doubao_api_key_here':
            return {
                'success': False,
                'error': '豆包API密钥未配置'
            }
        
        try:
            # 读取并编码图片
            with open(image_path, 'rb') as f:
                image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            return self._process_image_base64(image_base64)
            
        except FileNotFoundError:
            return {
                'success': False,
                'error': f'图片文件不存在: {image_path}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'图片处理失败: {str(e)}'
            }
    
    def extract_text_from_image_base64(self, image_base64: str) -> Dict[str, Any]:
        """
        使用豆包识别base64图片中的文本
        
        Args:
            image_base64: base64编码的图片数据
            
        Returns:
            {
                'success': bool,
                'text': str,  # 识别的文本
                'confidence': float,  # 置信度
                'error': str  # 错误信息
            }
        """
        if not self.api_key or self.api_key == 'your_doubao_api_key_here':
            return {
                'success': False,
                'error': '豆包API密钥未配置'
            }
        
        return self._process_image_base64(image_base64)
    
    def _process_image_base64(self, image_base64: str) -> Dict[str, Any]:
        """处理base64图片的内部方法 - 使用官方SDK"""
        if not self.client:
            return {
                'success': False,
                'error': '豆包SDK未正确初始化'
            }
        
        try:
            print(f"[OCR] 使用豆包官方SDK进行OCR识别")
            print(f"[Info] Endpoint: {self.endpoint_id}")
            
            # 优化：使用更短的提示词和更少的token，加快OCR识别速度
            response = self.client.chat.completions.create(
                model=self.endpoint_id,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "识别图中文字。"  # 优化：最简提示词
                            },
                            {
                                "type": "image_url", 
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=config.MAX_TOKENS,  # 优化：使用配置的token限制
                temperature=0.1
            )
            
            # 提取识别结果
            extracted_text = response.choices[0].message.content
            
            print(f"[Success] 豆包OCR识别成功!")
            print(f"[Text] 识别文本: {extracted_text[:100]}...")
            
            return {
                'success': True,
                'text': extracted_text,
                'confidence': 0.95,
                'source': '豆包视觉模型(官方SDK)'
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"[Error] 豆包OCR调用失败: {error_msg}")
            
            # 检查是否是内部服务器错误
            if "InternalServiceError" in error_msg or "500" in error_msg:
                return {
                    'success': False,
                    'error': '豆包服务暂时不可用，接入点可能正在部署中。请稍后重试或联系技术支持。'
                }
            elif "401" in error_msg or "认证" in error_msg:
                return {
                    'success': False,
                    'error': 'API认证失败，请检查API Key配置'
                }
            else:
                return {
                    'success': False,
                    'error': f'豆包OCR调用异常: {error_msg}'
                }
                
        except requests.Timeout:
            return {
                'success': False,
                'error': f'请求超时（超过{self.timeout}秒）'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'豆包调用异常: {str(e)}'
            }
    
    def _parse_extracted_info(self, text: str) -> Dict[str, str]:
        """解析提取的结构化信息"""
        info = {
            'question': '',
            'category': '',
            'key_info': ''
        }
        
        lines = text.split('\n')
        current_key = None
        
        for line in lines:
            line = line.strip()
            if '题目' in line and '文本' in line:
                current_key = 'question'
            elif '类型' in line:
                current_key = 'category'
            elif '关键信息' in line:
                current_key = 'key_info'
            elif line and current_key:
                info[current_key] += line + '\n'
        
        return info


class AIService:
    """AI服务统一接口"""
    
    def __init__(self):
        self.deepseek = DeepSeekSolver()
        self.doubao = DoubaoVision()
    
    def extract_text_from_image_base64(self, image_base64: str) -> Dict[str, Any]:
        """
        从base64图片中提取文本
        
        Args:
            image_base64: base64编码的图片数据
            
        Returns:
            OCR识别结果
        """
        return self.doubao.extract_text_from_image_base64(image_base64)
        
    def solve_with_image(self, image_path: str, category: Optional[str] = None) -> Dict[str, Any]:
        """
        处理带图片的题目：先用豆包识别，再用DeepSeek解答
        
        Args:
            image_path: 图片路径
            category: 题目类别
            
        Returns:
            完整的解答结果
        """
        result = {
            'success': False,
            'ocr_result': None,
            'answer_result': None,
            'error': None
        }
        
        # 步骤1: 使用豆包识别图片
        if config.ENABLE_IMAGE_OCR:
            print(f"[OCR] 使用豆包识别图片: {image_path}")
            ocr_result = self.doubao.extract_question_from_image(image_path)
            result['ocr_result'] = ocr_result
            
            if not ocr_result['success']:
                result['error'] = f"图片识别失败: {ocr_result['error']}"
                return result
            
            question_text = ocr_result.get('text', '')
            
            # 尝试从结构化信息中提取类别
            if not category and ocr_result.get('structured_info'):
                category_text = ocr_result['structured_info'].get('category', '').lower()
                if '微积分' in category_text or 'calculus' in category_text:
                    category = 'calculus'
                elif '物理' in category_text:
                    category = 'physics'
                elif '电路' in category_text:
                    category = 'circuit'
        else:
            result['error'] = '图像识别功能未启用'
            return result
        
        # 步骤2: 使用DeepSeek解答
        if config.ENABLE_AI_SOLVER and question_text:
            print(f"[AI] 使用DeepSeek解答题目...")
            answer_result = self.deepseek.solve_question(question_text, category)
            result['answer_result'] = answer_result
            
            if answer_result['success']:
                result['success'] = True
            else:
                result['error'] = f"解答失败: {answer_result['error']}"
        else:
            result['error'] = 'AI解答功能未启用或题目文本为空'
        
        return result
    
    def solve_with_text(self, question_text: str, category: Optional[str] = None) -> Dict[str, Any]:
        """
        处理纯文本题目：直接用DeepSeek解答
        
        Args:
            question_text: 题目文本
            category: 题目类别
            
        Returns:
            解答结果
        """
        if not config.ENABLE_AI_SOLVER:
            return {
                'success': False,
                'error': 'AI解答功能未启用'
            }
        
        print(f"[AI] 使用DeepSeek解答文本题目...")
        return self.deepseek.solve_question(question_text, category)


# 创建全局AI服务实例
ai_service = AIService()


if __name__ == '__main__':
    # 测试AI服务
    print("测试DeepSeek解题...")
    test_question = "求函数 f(x) = x^2 + 2x + 1 在 x=1 处的导数"
    result = ai_service.solve_with_text(test_question, 'calculus')
    
    if result['success']:
        print(f"\n[Success] 解答成功:")
        print(result['answer'])
    else:
        print(f"\n[Error] 解答失败: {result['error']}")
