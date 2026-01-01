"""
图像相似度匹配服务
使用感知哈希(pHash)和直方图比较算法
"""
import os
from PIL import Image
import hashlib
import io

# 图像缓存
_image_hash_cache = {}


def dhash(image, hash_size=8):
    """
    差值哈希算法(dHash)
    比较相邻像素的亮度差异，生成哈希值
    """
    # 转为灰度图并缩放
    image = image.convert('L').resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = list(image.getdata())
    
    # 计算差值
    diff = []
    for row in range(hash_size):
        for col in range(hash_size):
            left = pixels[row * (hash_size + 1) + col]
            right = pixels[row * (hash_size + 1) + col + 1]
            diff.append(1 if left > right else 0)
    
    # 转为16进制哈希
    hash_value = 0
    for bit in diff:
        hash_value = (hash_value << 1) | bit
    return hash_value


def phash(image, hash_size=8, highfreq_factor=4):
    """
    感知哈希算法(pHash)
    使用DCT变换，对图像内容变化更鲁棒
    """
    import_size = hash_size * highfreq_factor
    image = image.convert('L').resize((import_size, import_size), Image.Resampling.LANCZOS)
    pixels = list(image.getdata())
    
    # 简化版：使用均值代替DCT
    # 将图像分块，计算每块均值
    block_size = highfreq_factor
    blocks = []
    
    for by in range(hash_size):
        for bx in range(hash_size):
            block_sum = 0
            for y in range(block_size):
                for x in range(block_size):
                    idx = (by * block_size + y) * import_size + (bx * block_size + x)
                    block_sum += pixels[idx]
            blocks.append(block_sum / (block_size * block_size))
    
    # 计算均值
    avg = sum(blocks) / len(blocks)
    
    # 生成哈希
    hash_value = 0
    for block in blocks:
        hash_value = (hash_value << 1) | (1 if block > avg else 0)
    
    return hash_value


def average_hash(image, hash_size=8):
    """
    均值哈希算法(aHash)
    最简单快速的哈希算法
    """
    image = image.convert('L').resize((hash_size, hash_size), Image.Resampling.LANCZOS)
    pixels = list(image.getdata())
    avg = sum(pixels) / len(pixels)
    
    hash_value = 0
    for pixel in pixels:
        hash_value = (hash_value << 1) | (1 if pixel > avg else 0)
    
    return hash_value


def hamming_distance(hash1, hash2):
    """
    计算汉明距离
    两个哈希值不同位的数量
    """
    x = hash1 ^ hash2
    count = 0
    while x:
        count += 1
        x &= x - 1
    return count


def calculate_similarity(hash1, hash2, hash_size=8):
    """
    计算相似度 (0-1之间，1表示完全相同)
    """
    max_distance = hash_size * hash_size
    distance = hamming_distance(hash1, hash2)
    return 1 - (distance / max_distance)


def get_image_hash(image_path, algorithm='phash'):
    """
    获取图像哈希值（带缓存）
    
    Args:
        image_path: 图像路径
        algorithm: 算法类型 ('phash', 'dhash', 'ahash')
    
    Returns:
        哈希值
    """
    cache_key = f"{image_path}_{algorithm}"
    
    if cache_key in _image_hash_cache:
        return _image_hash_cache[cache_key]
    
    try:
        with Image.open(image_path) as img:
            if algorithm == 'phash':
                hash_value = phash(img)
            elif algorithm == 'dhash':
                hash_value = dhash(img)
            else:
                hash_value = average_hash(img)
        
        _image_hash_cache[cache_key] = hash_value
        return hash_value
    except Exception as e:
        print(f"[Error] Failed to hash image {image_path}: {e}")
        return None


def get_image_hash_from_bytes(image_bytes, algorithm='phash'):
    """
    从字节数据获取图像哈希值
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if algorithm == 'phash':
            return phash(img)
        elif algorithm == 'dhash':
            return dhash(img)
        else:
            return average_hash(img)
    except Exception as e:
        print(f"[Error] Failed to hash image from bytes: {e}")
        return None


def compare_images(image1_path, image2_path, algorithm='phash'):
    """
    比较两张图片的相似度
    
    Returns:
        相似度 (0-1之间)
    """
    hash1 = get_image_hash(image1_path, algorithm)
    hash2 = get_image_hash(image2_path, algorithm)
    
    if hash1 is None or hash2 is None:
        return 0.0
    
    return calculate_similarity(hash1, hash2)


def find_similar_images(query_image_path, image_folder, algorithm='phash', threshold=0.6):
    """
    在文件夹中查找相似图片
    
    Args:
        query_image_path: 查询图片路径
        image_folder: 图片文件夹路径
        algorithm: 哈希算法
        threshold: 相似度阈值
    
    Returns:
        相似图片列表 [(文件名, 相似度), ...]
    """
    query_hash = get_image_hash(query_image_path, algorithm)
    if query_hash is None:
        return []
    
    results = []
    
    # 支持的图片格式
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
    
    for filename in os.listdir(image_folder):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in valid_extensions:
            continue
        
        image_path = os.path.join(image_folder, filename)
        image_hash = get_image_hash(image_path, algorithm)
        
        if image_hash is not None:
            similarity = calculate_similarity(query_hash, image_hash)
            if similarity >= threshold:
                results.append((filename, similarity))
    
    # 按相似度降序排序
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def find_similar_from_bytes(query_bytes, image_folder, algorithm='phash', threshold=0.6):
    """
    从字节数据查找相似图片
    """
    query_hash = get_image_hash_from_bytes(query_bytes, algorithm)
    if query_hash is None:
        return []
    
    results = []
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
    
    for filename in os.listdir(image_folder):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in valid_extensions:
            continue
        
        image_path = os.path.join(image_folder, filename)
        image_hash = get_image_hash(image_path, algorithm)
        
        if image_hash is not None:
            similarity = calculate_similarity(query_hash, image_hash)
            if similarity >= threshold:
                results.append((filename, similarity))
    
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def clear_cache():
    """清除哈希缓存"""
    global _image_hash_cache
    _image_hash_cache = {}


def preload_image_hashes(image_folder, algorithm='phash'):
    """
    预加载文件夹中所有图片的哈希值
    用于启动时预热缓存
    """
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
    count = 0
    
    for filename in os.listdir(image_folder):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in valid_extensions:
            continue
        
        image_path = os.path.join(image_folder, filename)
        get_image_hash(image_path, algorithm)
        count += 1
    
    print(f"[Info] Preloaded {count} image hashes from {image_folder}")
    return count


# 测试代码
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) >= 3:
        img1, img2 = sys.argv[1], sys.argv[2]
        
        print(f"Comparing: {img1} vs {img2}")
        print(f"pHash similarity: {compare_images(img1, img2, 'phash'):.2%}")
        print(f"dHash similarity: {compare_images(img1, img2, 'dhash'):.2%}")
        print(f"aHash similarity: {compare_images(img1, img2, 'ahash'):.2%}")
    else:
        print("Usage: python image_matcher.py <image1> <image2>")
