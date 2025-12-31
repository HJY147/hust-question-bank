"""
OCR 识别服务
支持普通文字、数学公式、图形识别
"""
import cv2
import numpy as np
from PIL import Image
from typing import Dict, List, Tuple, Optional
import re

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    print("Warning: PaddleOCR not installed. OCR功能将受限")

try:
    from pix2tex.cli import LatexOCR
    PIX2TEX_AVAILABLE = True
except ImportError:
    PIX2TEX_AVAILABLE = False
    print("Warning: pix2tex not installed. 公式识别功能将受限")

from config import OCR_CONFIG, MATH_OCR_CONFIG, IMAGE_PREPROCESS


class OCRService:
    """OCR 识别服务类"""
    
    def __init__(self):
        # 初始化 PaddleOCR（文字识别）
        self.ocr = None
        if PADDLEOCR_AVAILABLE:
            # Some PaddleOCR versions may raise during pipeline/model setup
            # due to mismatched paddle/paddlex versions. Catch any exception
            # and fall back to SimpleOCRService to keep the system usable.
            try:
                paddle_args = dict(OCR_CONFIG)
                paddle_args.pop('use_gpu', None)
                try:
                    self.ocr = PaddleOCR(**paddle_args)
                except TypeError:
                    # older/newer versions may not accept kwargs
                    self.ocr = PaddleOCR()
            except Exception as e:
                print(f"PaddleOCR 初始化发生异常，已回退到简化 OCR：{e}")
                self.ocr = None
        
        # 初始化公式识别
        if PIX2TEX_AVAILABLE and MATH_OCR_CONFIG['enable']:
            try:
                self.math_ocr = LatexOCR()
            except:
                self.math_ocr = None
                print("Warning: 公式识别模型加载失败")
        else:
            self.math_ocr = None
    
    def recognize_image(self, image_path: str) -> Dict:
        """
        识别图片中的文字和公式
        
        Args:
            image_path: 图片路径
            
        Returns:
            识别结果字典，包含文字、公式、置信度等信息
        """
        # 预处理图像
        processed_img = self.preprocess_image(image_path)
        
        result = {
            'text': '',
            'formulas': [],
            'confidence': 0.0,
            'raw_ocr_result': [],
        }
        
        # 文字识别
        if self.ocr:
            try:
                ocr_result = self.ocr.ocr(processed_img, cls=True)
                result['raw_ocr_result'] = ocr_result
                
                # 提取文字和置信度
                text_lines = []
                confidences = []
                
                if ocr_result and len(ocr_result) > 0 and ocr_result[0]:
                    for line in ocr_result[0]:
                        if line and len(line) >= 2:
                            text = line[1][0]  # 识别的文字
                            conf = line[1][1]  # 置信度
                            text_lines.append(text)
                            confidences.append(conf)
                
                result['text'] = ' '.join(text_lines)
                result['confidence'] = np.mean(confidences) if confidences else 0.0
            except Exception as e:
                print(f"OCR识别错误: {e}")
                result['text'] = "[OCR识别失败]"
        
        # 公式识别
        if self.math_ocr:
            try:
                formulas = self.detect_and_recognize_formulas(processed_img)
                result['formulas'] = formulas
            except Exception as e:
                print(f"公式识别错误: {e}")
        
        return result
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        图像预处理
        
        Args:
            image_path: 图片路径
            
        Returns:
            预处理后的图像数组
        """
        # 读取图像
        img = cv2.imread(image_path)
        
        if img is None:
            raise ValueError(f"无法读取图像: {image_path}")
        
        # 调整大小
        if IMAGE_PREPROCESS['resize']:
            height, width = img.shape[:2]
            max_width, max_height = IMAGE_PREPROCESS['resize']
            
            # 保持宽高比
            scale = min(max_width / width, max_height / height)
            if scale < 1:
                new_width = int(width * scale)
                new_height = int(height * scale)
                img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # 去噪
        if IMAGE_PREPROCESS['denoise']:
            img = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
        
        # 增强对比度
        if IMAGE_PREPROCESS['enhance_contrast']:
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            img = cv2.merge([l, a, b])
            img = cv2.cvtColor(img, cv2.COLOR_LAB2BGR)
        
        # 二值化（可选）
        if IMAGE_PREPROCESS.get('binarize', False):
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
        
        return img
    
    def detect_and_recognize_formulas(self, image: np.ndarray) -> List[Dict]:
        """
        检测并识别图像中的数学公式
        
        Args:
            image: 图像数组
            
        Returns:
            公式列表，每个公式包含位置和LaTeX表示
        """
        formulas = []
        
        if not self.math_ocr:
            return formulas
        
        try:
            # 将 OpenCV 图像转换为 PIL Image
            if len(image.shape) == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image
            
            pil_img = Image.fromarray(image_rgb)
            
            # 识别公式
            latex = self.math_ocr(pil_img)
            
            if latex and latex.strip():
                formulas.append({
                    'latex': latex,
                    'confidence': 0.9,  # pix2tex 不提供置信度，使用默认值
                })
        except Exception as e:
            print(f"公式识别错误: {e}")
        
        return formulas
    
    def extract_text_features(self, ocr_result: Dict) -> str:
        """
        从OCR结果中提取文本特征
        用于后续的文本匹配
        
        Args:
            ocr_result: OCR识别结果
            
        Returns:
            特征文本字符串
        """
        features = []
        
        # 添加识别的文字
        if ocr_result['text']:
            features.append(ocr_result['text'])
        
        # 添加公式（LaTeX格式）
        for formula in ocr_result['formulas']:
            features.append(formula['latex'])
        
        return ' '.join(features)
    
    def batch_recognize(self, image_paths: List[str]) -> List[Dict]:
        """
        批量识别图像
        
        Args:
            image_paths: 图片路径列表
            
        Returns:
            识别结果列表
        """
        results = []
        for image_path in image_paths:
            try:
                result = self.recognize_image(image_path)
                result['image_path'] = image_path
                results.append(result)
            except Exception as e:
                print(f"识别失败 {image_path}: {e}")
                results.append({
                    'image_path': image_path,
                    'text': '',
                    'formulas': [],
                    'confidence': 0.0,
                    'error': str(e)
                })
        
        return results


class SimpleOCRService:
    """
    简化版 OCR 服务（当PaddleOCR不可用时使用）
    使用 pytesseract 或其他轻量级方案
    """
    
    def __init__(self):
        try:
            import pytesseract
            self.ocr = pytesseract
            self.available = True
        except ImportError:
            self.available = False
            print("Warning: 未安装任何OCR引擎")
    
    def recognize_image(self, image_path: str) -> Dict:
        """简单的图像识别"""
        if not self.available:
            return {
                'text': '[OCR不可用]',
                'formulas': [],
                'confidence': 0.0,
            }
        
        try:
            img = Image.open(image_path)
            text = self.ocr.image_to_string(img, lang='chi_sim+eng')
            
            return {
                'text': text.strip(),
                'formulas': [],
                'confidence': 0.8,
            }
        except Exception as e:
            return {
                'text': f'[识别失败: {e}]',
                'formulas': [],
                'confidence': 0.0,
            }


# 创建全局OCR服务实例
def get_ocr_service():
    """获取OCR服务实例"""
    # Try to initialize full OCR service; if it fails or is not usable,
    # fall back to SimpleOCRService (pytesseract) when available.
    try:
        service = OCRService()
        if service.ocr is None and service.math_ocr is None:
            # fallback
            return SimpleOCRService()
        return service
    except Exception:
        return SimpleOCRService()
