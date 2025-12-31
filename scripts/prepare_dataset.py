"""
数据预处理脚本
将手写作业图片处理成可用的训练集
"""
import os
import cv2
import numpy as np
from PIL import Image
import argparse
from pathlib import Path


class ImagePreprocessor:
    """图像预处理器"""
    
    def __init__(self):
        pass
    
    def enhance_image(self, image_path: str, output_path: str):
        """
        增强图像质量
        - 去噪
        - 增强对比度
        - 自动调整亮度
        - 去除阴影
        """
        # 读取图像
        img = cv2.imread(image_path)
        
        if img is None:
            print(f"无法读取图像: {image_path}")
            return False
        
        # 1. 去噪
        img = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
        
        # 2. 转换到LAB色彩空间增强对比度
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # 应用CLAHE (对比度限制自适应直方图均衡化)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # 合并通道
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # 3. 自动白平衡
        enhanced = self.auto_white_balance(enhanced)
        
        # 4. 锐化
        kernel = np.array([[-1,-1,-1],
                          [-1, 9,-1],
                          [-1,-1,-1]])
        enhanced = cv2.filter2D(enhanced, -1, kernel)
        
        # 保存处理后的图像
        cv2.imwrite(output_path, enhanced)
        print(f"已处理: {image_path} -> {output_path}")
        
        return True
    
    def auto_white_balance(self, img):
        """自动白平衡"""
        result = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        avg_a = np.average(result[:, :, 1])
        avg_b = np.average(result[:, :, 2])
        result[:, :, 1] = result[:, :, 1] - ((avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1)
        result[:, :, 2] = result[:, :, 2] - ((avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1)
        result = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)
        return result
    
    def crop_to_content(self, image_path: str, output_path: str, padding=20):
        """
        自动裁剪图像到内容区域
        去除多余的空白边缘
        """
        img = cv2.imread(image_path)
        
        if img is None:
            print(f"无法读取图像: {image_path}")
            return False
        
        # 转换为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 二值化
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            print(f"未找到内容区域: {image_path}")
            return False
        
        # 获取最大的边界框
        x, y, w, h = cv2.boundingRect(np.vstack(contours))
        
        # 添加padding
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(img.shape[1] - x, w + 2 * padding)
        h = min(img.shape[0] - y, h + 2 * padding)
        
        # 裁剪
        cropped = img[y:y+h, x:x+w]
        
        # 保存
        cv2.imwrite(output_path, cropped)
        print(f"已裁剪: {image_path} -> {output_path}")
        
        return True
    
    def rotate_correct(self, image_path: str, output_path: str):
        """
        自动矫正图像旋转角度
        """
        img = cv2.imread(image_path)
        
        if img is None:
            return False
        
        # 转换为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 边缘检测
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # 霍夫变换检测直线
        lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
        
        if lines is None:
            cv2.imwrite(output_path, img)
            return True
        
        # 计算平均角度
        angles = []
        for line in lines[:10]:  # 只使用前10条线
            rho, theta = line[0]
            angle = (theta * 180 / np.pi) - 90
            angles.append(angle)
        
        median_angle = np.median(angles)
        
        # 如果角度较小，进行旋转矫正
        if abs(median_angle) > 0.5:
            center = (img.shape[1] // 2, img.shape[0] // 2)
            matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            rotated = cv2.warpAffine(img, matrix, (img.shape[1], img.shape[0]),
                                    flags=cv2.INTER_CUBIC,
                                    borderMode=cv2.BORDER_REPLICATE)
            cv2.imwrite(output_path, rotated)
            print(f"已矫正旋转 {median_angle:.2f}度: {image_path}")
        else:
            cv2.imwrite(output_path, img)
        
        return True
    
    def batch_process(self, input_dir: str, output_dir: str, 
                     enhance=True, crop=True, rotate=True):
        """
        批量处理图像
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            enhance: 是否增强图像
            crop: 是否自动裁剪
            rotate: 是否旋转矫正
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # 支持的图像格式
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
        
        # 遍历输入目录
        input_path = Path(input_dir)
        image_files = [f for f in input_path.iterdir() 
                      if f.suffix.lower() in image_extensions]
        
        print(f"找到 {len(image_files)} 个图像文件")
        
        for i, image_file in enumerate(image_files, 1):
            print(f"\n处理 {i}/{len(image_files)}: {image_file.name}")
            
            temp_path = str(image_file)
            output_path = os.path.join(output_dir, image_file.name)
            
            try:
                # 旋转矫正
                if rotate:
                    temp_output = os.path.join(output_dir, f"temp_{image_file.name}")
                    self.rotate_correct(temp_path, temp_output)
                    temp_path = temp_output
                
                # 裁剪
                if crop:
                    temp_output = os.path.join(output_dir, f"temp2_{image_file.name}")
                    self.crop_to_content(temp_path, temp_output)
                    if os.path.exists(temp_output):
                        temp_path = temp_output
                
                # 增强
                if enhance:
                    self.enhance_image(temp_path, output_path)
                else:
                    if temp_path != str(image_file):
                        os.rename(temp_path, output_path)
                
                # 清理临时文件
                for temp_file in Path(output_dir).glob("temp*.jpg"):
                    temp_file.unlink()
                for temp_file in Path(output_dir).glob("temp*.png"):
                    temp_file.unlink()
                
            except Exception as e:
                print(f"处理失败: {e}")
        
        print(f"\n批量处理完成! 输出目录: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description='图像预处理工具')
    parser.add_argument('--input', '-i', required=True, help='输入目录')
    parser.add_argument('--output', '-o', required=True, help='输出目录')
    parser.add_argument('--no-enhance', action='store_true', help='不进行图像增强')
    parser.add_argument('--no-crop', action='store_true', help='不进行自动裁剪')
    parser.add_argument('--no-rotate', action='store_true', help='不进行旋转矫正')
    
    args = parser.parse_args()
    
    preprocessor = ImagePreprocessor()
    preprocessor.batch_process(
        input_dir=args.input,
        output_dir=args.output,
        enhance=not args.no_enhance,
        crop=not args.no_crop,
        rotate=not args.no_rotate
    )


if __name__ == '__main__':
    main()
