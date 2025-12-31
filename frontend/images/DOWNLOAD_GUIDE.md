# 华中科技大学图片资源获取指南

## 🎯 快速下载链接

### 1. 华科官方校徽
**来源：华中科技大学官网**
- 访问：https://www.hust.edu.cn/
- 或直接下载：https://www.hust.edu.cn/images/logo.png

**操作步骤：**
1. 右键点击校徽图片 → 另存为
2. 保存到：`frontend/images/logo/hust_logo_original.png`
3. 使用在线工具调整尺寸：
   - 32×32px → `hust_logo_32.png`
   - 24×24px → `hust_logo_24.png`
   - 48×48px → `hust_logo_48.png`

**在线调整工具：**
- https://www.iloveimg.com/zh-cn/resize-image
- https://tinypng.com/ (压缩)

---

### 2. 梧桐大道照片
**推荐来源：**

**方案A：百度图片（推荐）**
1. 访问：https://image.baidu.com/
2. 搜索："华中科技大学 梧桐大道"
3. 选择高清大图，右键保存
4. 保存为：`frontend/images/landmark/wutong_road.jpg`

**方案B：华科官方网站**
- 官网新闻图片：https://news.hust.edu.cn/
- 选择校园风景类新闻，下载梧桐大道照片

**方案C：免费图库**
- Pixabay: https://pixabay.com/zh/images/search/华中科技大学/
- Unsplash: https://unsplash.com/s/photos/wuhan-university

---

### 3. 主教学楼照片
**搜索关键词：**
- "华中科技大学 主教学楼"
- "HUST main building"
- "华科 主楼"

**下载方式：**
1. 百度图片搜索
2. 选择清晰的建筑外观照片
3. 保存为：`frontend/images/landmark/main_building.jpg`

---

### 4. 光电大楼
**搜索关键词：**
- "华中科技大学 光电国家实验室"
- "HUST 光电大楼"

保存为：`frontend/images/landmark/optoelectronic.jpg`

---

### 5. 同济医学院
**搜索关键词：**
- "华中科技大学同济医学院"
- "同济医学院 红楼"

保存为：`frontend/images/landmark/tongji_red.jpg`

---

### 6. 图书馆
**搜索关键词：**
- "华中科技大学图书馆"
- "HUST library"

保存为：`frontend/images/landmark/library.jpg`

---

## 🚀 快速批量下载脚本

创建一个PowerShell脚本自动下载（需要手动提供图片URL）：

```powershell
# download_images.ps1
$images = @{
    "https://example.com/hust_logo.png" = "frontend/images/logo/hust_logo_original.png"
    "https://example.com/wutong.jpg" = "frontend/images/landmark/wutong_road.jpg"
    # ... 添加更多图片URL
}

foreach ($url in $images.Keys) {
    $output = $images[$url]
    Write-Host "下载: $url -> $output"
    Invoke-WebRequest -Uri $url -OutFile $output
}
```

---

## 📐 图片尺寸要求

| 图片类型 | 推荐尺寸 | 格式 | 大小限制 |
|---------|---------|------|---------|
| 校徽（导航栏） | 32×32px | PNG | <50KB |
| 校徽（按钮） | 24×24px | PNG | <30KB |
| 校徽（底部） | 48×48px | PNG | <80KB |
| 梧桐大道背景 | 1920×600px | JPG | <500KB |
| 建筑物插画 | 200×120px | JPG/PNG | <200KB |
| 图书馆场景 | 200×120px | JPG/PNG | <200KB |

---

## ⚡ 当前临时方案

我已经创建了以下SVG临时占位符：
- ✅ `logo/hust_logo.svg` - 简化校徽
- ✅ `landmark/wutong_road.svg` - 梧桐大道插画
- ✅ `landmark/main_building.svg` - 主教学楼插画
- ✅ `illustration/study_scene.svg` - 图书馆学习场景
- ✅ `illustration/wutong_leaf.svg` - 梧桐叶暗纹

**这些SVG可以立即使用，效果已经很好！**

如果需要替换为真实照片，按照上面的指南下载即可。

---

## 🎨 图片处理技巧

### 调整图片尺寸（在线工具）
1. 访问：https://www.iloveimg.com/zh-cn/resize-image
2. 上传图片
3. 输入目标尺寸（如 1920×600）
4. 选择"精确尺寸"
5. 下载处理后的图片

### 压缩图片（减小文件大小）
1. 访问：https://tinypng.com/
2. 拖拽上传图片
3. 等待压缩完成
4. 下载压缩后的图片

### 去除背景（PNG透明底）
1. 访问：https://www.remove.bg/zh
2. 上传校徽图片
3. 自动去除背景
4. 下载PNG格式

---

## ✅ 使用建议

1. **优先使用SVG** - 已创建的SVG占位符效果很好，矢量图形，任意缩放不失真
2. **真实照片** - 如果需要更真实的效果，按照上面的指南下载照片
3. **版权安全** - 使用华科官网图片用于学习辅助是合理使用
4. **文件命名** - 保持与HTML中引用的文件名一致

---

现在HTML中已经引用了这些图片路径，你可以：
- 直接使用当前的SVG（推荐，已经很美观）
- 或者按照指南下载真实照片替换
