# PDF转图片工具
# 使用方法: python pdf转图片.py 文件路径.pdf

import sys
import os

try:
    from PIL import Image
    import fitz  # PyMuPDF
except ImportError:
    print("❌ 缺少依赖包！")
    print("\n请先安装依赖:")
    print("pip install PyMuPDF Pillow -i https://pypi.tuna.tsinghua.edu.cn/simple")
    sys.exit(1)

def pdf_to_images(pdf_path, output_folder="pdf_output"):
    """将PDF转换为图片"""
    if not os.path.exists(pdf_path):
        print(f"❌ 文件不存在: {pdf_path}")
        return
    
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    # 打开PDF
    pdf_document = fitz.open(pdf_path)
    
    print(f"📄 PDF总页数: {len(pdf_document)}")
    
    # 转换每一页
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        
        # 设置缩放比例（提高分辨率）
        zoom = 2  # 2倍缩放
        mat = fitz.Matrix(zoom, zoom)
        
        # 渲染为图片
        pix = page.get_pixmap(matrix=mat)
        
        # 保存图片
        output_path = os.path.join(output_folder, f"page_{page_num + 1:03d}.png")
        pix.save(output_path)
        
        print(f"✓ 第{page_num + 1}页 → {output_path}")
    
    pdf_document.close()
    print(f"\n✅ 完成！图片已保存到: {output_folder}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python pdf转图片.py PDF文件路径")
        print("示例: python pdf转图片.py 题目.pdf")
    else:
        pdf_to_images(sys.argv[1])
