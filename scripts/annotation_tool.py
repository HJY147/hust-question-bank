"""
数据标注工具
用于将手写作业照片转换为可用的训练数据
提供GUI界面进行快速标注
"""
import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import cv2
import numpy as np

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class QuestionAnnotationTool:
    """题目标注工具GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("📝 题目标注工具")
        self.root.geometry("1400x900")
        
        # 数据
        self.image_files = []
        self.current_index = 0
        self.annotations = {}
        self.output_dir = None
        
        # 类别选项
        self.categories = [
            "calculus",           # 微积分
            "complex_analysis",   # 复变函数
            "physics",            # 大学物理
            "circuit",            # 电路理论
            "mechanics",          # 理论力学
            "linear_algebra",     # 线性代数
            "probability",        # 概率论
            "other"               # 其他
        ]
        
        self.difficulties = ["easy", "medium", "hard"]
        
        self._create_ui()
    
    def _create_ui(self):
        """创建界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：图片显示区
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 工具栏
        toolbar = ttk.Frame(left_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar, text="📂 打开文件夹", command=self.open_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📁 设置输出目录", command=self.set_output_dir).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 保存全部", command=self.save_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📤 导出数据", command=self.export_data).pack(side=tk.LEFT, padx=2)
        
        # 进度显示
        self.progress_label = ttk.Label(toolbar, text="未加载图片")
        self.progress_label.pack(side=tk.RIGHT, padx=10)
        
        # 图片画布
        canvas_frame = ttk.Frame(left_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg='gray90')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 导航按钮
        nav_frame = ttk.Frame(left_frame)
        nav_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(nav_frame, text="⬅ 上一张", command=self.prev_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="下一张 ➡", command=self.next_image).pack(side=tk.LEFT, padx=5)
        
        # 跳转
        ttk.Label(nav_frame, text="跳转到:").pack(side=tk.LEFT, padx=(20, 5))
        self.jump_var = tk.StringVar()
        self.jump_entry = ttk.Entry(nav_frame, textvariable=self.jump_var, width=8)
        self.jump_entry.pack(side=tk.LEFT)
        ttk.Button(nav_frame, text="跳转", command=self.jump_to).pack(side=tk.LEFT, padx=5)
        
        # 右侧：标注区
        right_frame = ttk.Frame(main_frame, width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_frame.pack_propagate(False)
        
        # 文件名
        ttk.Label(right_frame, text="当前文件:").pack(anchor=tk.W)
        self.filename_var = tk.StringVar(value="无")
        ttk.Label(right_frame, textvariable=self.filename_var, font=("", 10, "bold")).pack(anchor=tk.W)
        
        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # 题目ID
        ttk.Label(right_frame, text="题目ID:").pack(anchor=tk.W)
        self.question_id_var = tk.StringVar()
        ttk.Entry(right_frame, textvariable=self.question_id_var, width=30).pack(fill=tk.X, pady=(0, 10))
        
        # 类别
        ttk.Label(right_frame, text="科目类别:").pack(anchor=tk.W)
        self.category_var = tk.StringVar(value="other")
        category_combo = ttk.Combobox(right_frame, textvariable=self.category_var, values=self.categories, state="readonly")
        category_combo.pack(fill=tk.X, pady=(0, 10))
        
        # 难度
        ttk.Label(right_frame, text="难度:").pack(anchor=tk.W)
        self.difficulty_var = tk.StringVar(value="medium")
        diff_frame = ttk.Frame(right_frame)
        diff_frame.pack(fill=tk.X, pady=(0, 10))
        for diff in self.difficulties:
            ttk.Radiobutton(diff_frame, text=diff, variable=self.difficulty_var, value=diff).pack(side=tk.LEFT, padx=5)
        
        # 标签
        ttk.Label(right_frame, text="标签 (逗号分隔):").pack(anchor=tk.W)
        self.tags_var = tk.StringVar()
        ttk.Entry(right_frame, textvariable=self.tags_var, width=30).pack(fill=tk.X, pady=(0, 10))
        
        # 题目文本 (OCR结果或手动输入)
        ttk.Label(right_frame, text="题目文本:").pack(anchor=tk.W)
        self.question_text = scrolledtext.ScrolledText(right_frame, height=6, width=40)
        self.question_text.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(right_frame, text="🔍 OCR识别", command=self.run_ocr).pack(fill=tk.X, pady=(0, 10))
        
        ttk.Separator(right_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # 答案
        ttk.Label(right_frame, text="答案 (支持LaTeX):").pack(anchor=tk.W)
        self.answer_text = scrolledtext.ScrolledText(right_frame, height=10, width=40)
        self.answer_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 保存按钮
        ttk.Button(right_frame, text="💾 保存当前标注", command=self.save_current).pack(fill=tk.X)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 绑定键盘快捷键
        self.root.bind('<Left>', lambda e: self.prev_image())
        self.root.bind('<Right>', lambda e: self.next_image())
        self.root.bind('<Control-s>', lambda e: self.save_current())
    
    def open_folder(self):
        """打开图片文件夹"""
        folder = filedialog.askdirectory(title="选择题目图片文件夹")
        if not folder:
            return
        
        # 获取所有图片
        extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
        self.image_files = sorted([
            os.path.join(folder, f) for f in os.listdir(folder)
            if os.path.splitext(f)[1].lower() in extensions
        ])
        
        if not self.image_files:
            messagebox.showwarning("警告", "文件夹中没有找到图片文件")
            return
        
        self.current_index = 0
        self.load_current_image()
        self.update_progress()
        
        # 尝试加载已有标注
        annotation_file = os.path.join(folder, 'annotations.json')
        if os.path.exists(annotation_file):
            try:
                with open(annotation_file, 'r', encoding='utf-8') as f:
                    self.annotations = json.load(f)
                self.status_var.set(f"已加载 {len(self.annotations)} 条标注")
            except:
                pass
        
        self.status_var.set(f"已加载 {len(self.image_files)} 张图片")
    
    def set_output_dir(self):
        """设置输出目录"""
        folder = filedialog.askdirectory(title="选择输出目录")
        if folder:
            self.output_dir = folder
            self.status_var.set(f"输出目录: {folder}")
    
    def load_current_image(self):
        """加载当前图片"""
        if not self.image_files:
            return
        
        image_path = self.image_files[self.current_index]
        self.filename_var.set(os.path.basename(image_path))
        
        # 加载并显示图片
        try:
            img = Image.open(image_path)
            
            # 调整大小以适应画布
            canvas_width = self.canvas.winfo_width() or 800
            canvas_height = self.canvas.winfo_height() or 600
            
            ratio = min(canvas_width / img.width, canvas_height / img.height)
            new_size = (int(img.width * ratio * 0.9), int(img.height * ratio * 0.9))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            self.photo = ImageTk.PhotoImage(img)
            self.canvas.delete("all")
            self.canvas.create_image(
                canvas_width // 2, canvas_height // 2,
                image=self.photo, anchor=tk.CENTER
            )
        except Exception as e:
            self.status_var.set(f"图片加载失败: {e}")
        
        # 加载已有标注
        self.load_annotation(image_path)
    
    def load_annotation(self, image_path):
        """加载图片的标注数据"""
        # 清空当前表单
        self.question_text.delete('1.0', tk.END)
        self.answer_text.delete('1.0', tk.END)
        
        filename = os.path.basename(image_path)
        
        # 默认ID为文件名(无扩展名)
        default_id = os.path.splitext(filename)[0]
        self.question_id_var.set(default_id)
        
        if filename in self.annotations:
            ann = self.annotations[filename]
            self.question_id_var.set(ann.get('question_id', default_id))
            self.category_var.set(ann.get('category', 'other'))
            self.difficulty_var.set(ann.get('difficulty', 'medium'))
            self.tags_var.set(','.join(ann.get('tags', [])))
            self.question_text.insert('1.0', ann.get('question_text', ''))
            self.answer_text.insert('1.0', ann.get('answer', ''))
    
    def save_current(self):
        """保存当前标注"""
        if not self.image_files:
            return
        
        filename = os.path.basename(self.image_files[self.current_index])
        
        self.annotations[filename] = {
            'question_id': self.question_id_var.get(),
            'category': self.category_var.get(),
            'difficulty': self.difficulty_var.get(),
            'tags': [t.strip() for t in self.tags_var.get().split(',') if t.strip()],
            'question_text': self.question_text.get('1.0', tk.END).strip(),
            'answer': self.answer_text.get('1.0', tk.END).strip(),
            'image_file': filename,
            'annotated_at': datetime.now().isoformat()
        }
        
        self.status_var.set(f"已保存: {filename}")
    
    def save_all(self):
        """保存所有标注到文件"""
        if not self.image_files:
            return
        
        # 先保存当前
        self.save_current()
        
        # 保存到文件夹
        folder = os.path.dirname(self.image_files[0])
        annotation_file = os.path.join(folder, 'annotations.json')
        
        with open(annotation_file, 'w', encoding='utf-8') as f:
            json.dump(self.annotations, f, ensure_ascii=False, indent=2)
        
        self.status_var.set(f"已保存 {len(self.annotations)} 条标注到 {annotation_file}")
        messagebox.showinfo("保存成功", f"已保存 {len(self.annotations)} 条标注")
    
    def export_data(self):
        """导出数据到题库格式"""
        if not self.output_dir:
            self.set_output_dir()
            if not self.output_dir:
                return
        
        if not self.annotations:
            messagebox.showwarning("警告", "没有标注数据可导出")
            return
        
        # 创建目录结构
        question_bank_dir = os.path.join(self.output_dir, 'question_bank')
        answers_dir = os.path.join(self.output_dir, 'answers')
        os.makedirs(question_bank_dir, exist_ok=True)
        os.makedirs(answers_dir, exist_ok=True)
        
        exported = 0
        source_folder = os.path.dirname(self.image_files[0]) if self.image_files else ''
        
        for filename, ann in self.annotations.items():
            question_id = ann.get('question_id', os.path.splitext(filename)[0])
            
            # 复制图片
            src_image = os.path.join(source_folder, filename)
            if os.path.exists(src_image):
                ext = os.path.splitext(filename)[1]
                dst_image = os.path.join(question_bank_dir, f"{question_id}{ext}")
                shutil.copy2(src_image, dst_image)
            
            # 保存答案
            answer = ann.get('answer', '')
            if answer:
                answer_file = os.path.join(answers_dir, f"{question_id}.txt")
                with open(answer_file, 'w', encoding='utf-8') as f:
                    f.write(answer)
            
            exported += 1
        
        # 保存元数据
        metadata = {
            'questions': list(self.annotations.values()),
            'exported_at': datetime.now().isoformat(),
            'total_count': exported
        }
        
        metadata_file = os.path.join(self.output_dir, 'metadata.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        self.status_var.set(f"已导出 {exported} 道题目")
        messagebox.showinfo("导出成功", f"已导出 {exported} 道题目到\n{self.output_dir}")
    
    def run_ocr(self):
        """运行OCR识别"""
        if not self.image_files:
            return
        
        image_path = self.image_files[self.current_index]
        self.status_var.set("正在识别...")
        self.root.update()
        
        try:
            # 导入OCR服务
            from backend.ocr_service import get_ocr_service
            ocr_service = get_ocr_service()
            
            result = ocr_service.recognize_image(image_path)
            
            # 填充结果
            self.question_text.delete('1.0', tk.END)
            self.question_text.insert('1.0', result.get('text', ''))
            
            self.status_var.set(f"OCR完成，置信度: {result.get('confidence', 0):.2%}")
            
        except Exception as e:
            self.status_var.set(f"OCR失败: {e}")
            messagebox.showerror("OCR错误", str(e))
    
    def prev_image(self):
        """上一张图片"""
        if not self.image_files:
            return
        
        self.save_current()
        self.current_index = (self.current_index - 1) % len(self.image_files)
        self.load_current_image()
        self.update_progress()
    
    def next_image(self):
        """下一张图片"""
        if not self.image_files:
            return
        
        self.save_current()
        self.current_index = (self.current_index + 1) % len(self.image_files)
        self.load_current_image()
        self.update_progress()
    
    def jump_to(self):
        """跳转到指定图片"""
        try:
            index = int(self.jump_var.get()) - 1
            if 0 <= index < len(self.image_files):
                self.save_current()
                self.current_index = index
                self.load_current_image()
                self.update_progress()
            else:
                messagebox.showwarning("警告", "索引超出范围")
        except ValueError:
            messagebox.showwarning("警告", "请输入有效数字")
    
    def update_progress(self):
        """更新进度显示"""
        if self.image_files:
            annotated = len(self.annotations)
            total = len(self.image_files)
            self.progress_label.config(
                text=f"{self.current_index + 1}/{total} (已标注: {annotated})"
            )


def main():
    """主函数"""
    root = tk.Tk()
    app = QuestionAnnotationTool(root)
    root.mainloop()


if __name__ == '__main__':
    main()
