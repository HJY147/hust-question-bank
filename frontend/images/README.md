# HUST专属搜题系统 - 图片资源包说明文档

## 📁 目录结构

图片资源已按规范创建在 `frontend/images/` 目录下：

```
frontend/images/
├── logo/                    # 华科校徽相关
│   ├── hust_logo_32.png    # 导航栏校徽（32×32px）
│   ├── hust_logo_24.png    # 按钮旁校徽（24×24px）
│   └── hust_logo_48.png    # 底部校徽（48×48px）
├── landmark/                # 华科校园地标
│   ├── wutong_road.jpg     # 梧桐大道背景（1920×600px）
│   ├── main_building.png   # 主教学楼插画（200×120px）
│   ├── optoelectronic.png  # 光电大楼插画（200×120px）
│   ├── tongji_red.png      # 同济医学院红楼插画（200×120px）
│   └── library.png         # 图书馆学习场景插画（200×120px）
├── icon/                    # 功能图标
│   ├── search_text.svg     # 文字搜题图标
│   ├── search_camera.svg   # 拍照搜题图标
│   ├── search_voice.svg    # 语音搜题图标
│   ├── collect.svg         # 收藏图标
│   ├── download.svg        # 下载图标
│   └── night_mode.svg      # 夜间模式图标
├── illustration/            # 装饰插画
│   ├── wutong_leaf.png     # 梧桐叶暗纹（透明底）
│   ├── exam_scene.png      # 考场插画（200×120px）
│   └── study_scene.png     # 图书馆学习插画（200×120px）
└── background/              # 背景图
    ├── home_bg.png         # 首页搜题区背景（1920×1080px）
    └── footer_bg.png       # 底部背景（1920×120px）
```

## 📥 图片资源获取指南

### 1. 华科校徽（logo/）

**来源：** 华中科技大学官网
**网址：** https://www.hust.edu.cn/

**获取步骤：**
1. 访问华科官网，找到"学校标识"或"校徽下载"页面
2. 下载官方标准版校徽（通常为PNG格式，透明底）
3. 使用图片编辑工具（Photoshop/GIMP）调整尺寸：
   - `hust_logo_32.png` → 32×32像素
   - `hust_logo_24.png` → 24×24像素
   - `hust_logo_48.png` → 48×48像素
4. 保持透明底，保存为PNG格式
5. 确保图片质量清晰，边缘无锯齿

**注意事项：**
- ✅ 仅使用官方标准版，禁止修改配色/比例
- ✅ 仅用于非商用校园服务
- ❌ 禁止变形、改色、添加效果

---

### 2. 校园地标（landmark/）

#### 2.1 梧桐大道背景（wutong_road.jpg）

**来源：** 免费可商用图库
**推荐网站：**
- Pixabay: https://pixabay.com/
- Unsplash: https://unsplash.com/
- Pexels: https://www.pexels.com/

**搜索关键词：**
- "hua zhong university"
- "wutong road"
- "autumn leaves university"
- "campus road"

**处理要求：**
- 尺寸：1920×600px（横向裁剪）
- 格式：JPG，质量≥85%
- 色调：自然饱和，适合做背景（不要过于鲜艳）
- 可添加半透明遮罩（#005AA7, 透明度20%）增强品牌感

#### 2.2 建筑物插画（main_building.png等）

**来源：** 免费插画平台
**推荐网站：**
- 阿里图标库 iconfont: https://iconfont.cn/
- undraw: https://undraw.co/illustrations
- freepik（免费版）: https://www.freepik.com/

**获取步骤：**
1. 搜索关键词："building", "university", "campus", "architecture"
2. 选择扁平化风格插画（flat design）
3. 下载SVG或PNG格式
4. 使用图片编辑工具调整为200×120px
5. 配色调整为华科色系（蓝#005AA7为主色）
6. 保存为PNG格式，透明底

**替代方案（如果找不到合适插画）：**
- 使用纯色卡片 + 文字说明
- 使用图标 + 渐变背景
- 自行绘制简化版建筑轮廓

---

### 3. 功能图标（icon/）

**来源：** 阿里图标库（iconfont）
**网址：** https://iconfont.cn/

**获取步骤：**
1. 访问 iconfont.cn，注册账号
2. 搜索对应图标：
   - search_text.svg → 搜索"文字"、"text"
   - search_camera.svg → 搜索"相机"、"camera"
   - search_voice.svg → 搜索"麦克风"、"microphone"
   - collect.svg → 搜索"收藏"、"star"
   - download.svg → 搜索"下载"、"download"
   - night_mode.svg → 搜索"月亮"、"moon"
3. 选择线性风格（outline style）图标
4. 下载SVG格式
5. 使用代码编辑器打开SVG，修改颜色为 `#005AA7`
6. 保存到对应目录

**SVG颜色修改示例：**
```svg
<!-- 原始 -->
<svg fill="#000000" ...>

<!-- 修改为HUST蓝 -->
<svg fill="#005AA7" ...>
```

---

### 4. 装饰插画（illustration/）

#### 4.1 梧桐叶暗纹（wutong_leaf.png）

**来源：** 免费矢量图库
**推荐网站：**
- Freepik: https://www.freepik.com/
- Vecteezy: https://www.vecteezy.com/

**搜索关键词：**
- "leaf pattern"
- "botanical pattern"
- "tree leaf transparent"

**处理要求：**
- 格式：PNG，透明底
- 尺寸：512×512px（可平铺）
- 透明度：≤20%（在CSS中设置 opacity: 0.2）
- 颜色：灰色系或蓝色系

#### 4.2 场景插画（exam_scene.png, study_scene.png）

**来源：** undraw 插画库
**网址：** https://undraw.co/illustrations

**获取步骤：**
1. 访问 undraw.co
2. 搜索关键词："study", "exam", "student", "library"
3. 在右上角颜色选择器中输入 `#005AA7`（HUST蓝）
4. 下载SVG格式
5. 使用在线工具转换为PNG：https://cloudconvert.com/svg-to-png
6. 调整尺寸为200×120px
7. 保存到对应目录

---

### 5. 背景图（background/）

#### 5.1 首页搜题区背景（home_bg.png）

**来源：** 自行制作或使用图片生成工具

**方案A：使用CSS渐变（推荐）**
```css
background: linear-gradient(135deg, #005AA7 0%, #0066cc 50%, #F5F7FA 100%);
```
优点：无需图片文件，加载快，可自定义

**方案B：使用现有图片**
- 从 landmark/ 中选择一张，添加渐变遮罩
- 使用Photoshop/Figma制作渐变背景
- 尺寸：1920×1080px
- 格式：PNG或JPG（压缩后≤500KB）

#### 5.2 底部背景（footer_bg.png）

**推荐方案：** 梧桐叶暗纹平铺 + 半透明遮罩

**制作步骤：**
1. 使用 `illustration/wutong_leaf.png` 作为基础
2. 平铺为1920×120px
3. 添加半透明白色遮罩（opacity: 0.8）
4. 保存为PNG格式

**替代方案：** 直接使用CSS
```css
background: linear-gradient(to right, #F5F7FA 0%, #E6F2FF 100%);
```

---

## 🎨 图片处理工具推荐

### 在线工具
1. **TinyPNG** - 图片压缩：https://tinypng.com/
2. **CloudConvert** - 格式转换：https://cloudconvert.com/
3. **Photopea** - 在线PS：https://www.photopea.com/
4. **Remove.bg** - 去背景：https://www.remove.bg/
5. **Figma** - 设计工具（免费）：https://www.figma.com/

### 本地工具
1. **Photoshop** - 专业图片编辑
2. **GIMP** - 免费开源替代品
3. **XnConvert** - 批量处理
4. **Inkscape** - SVG编辑

---

## ✅ 图片验收清单

### 尺寸规范
- [ ] 导航栏校徽：32×32px
- [ ] 按钮旁校徽：24×24px
- [ ] 底部校徽：48×48px
- [ ] 地标插画：200×120px
- [ ] 梧桐大道背景：1920×600px
- [ ] 首屏背景：1920×1080px
- [ ] 底部背景：1920×120px

### 格式要求
- [ ] 校徽：PNG，透明底
- [ ] 功能图标：SVG
- [ ] 插画：PNG，透明底
- [ ] 背景图：JPG（≤500KB）或PNG

### 色彩规范
- [ ] 图标颜色适配HUST蓝（#005AA7）
- [ ] 插画主色调为华科色系
- [ ] 背景图不影响文字可读性

### 合规要求
- [ ] 校徽来自官方，未修改
- [ ] 所有图片来源可商用/合规
- [ ] 移动端图片已压缩（≤200KB）
- [ ] 已标注「非商用，仅用于华科学生学习辅助」

---

## 🚀 快速开始

如果暂时没有图片资源，可以：

### 临时方案（开发阶段）
1. 校徽：使用Unicode emoji "🎓" 或 "🏛️" 代替
2. 地标：使用纯色卡片 + 文字标识
3. 图标：使用Bootstrap Icons或Emoji
4. 背景：使用CSS渐变

### 示例代码（无图片版本）
```html
<!-- 校徽替代 -->
<span style="font-size: 32px;">🎓</span>

<!-- 地标卡片替代 -->
<div style="background: linear-gradient(135deg, #005AA7, #0066cc); 
            color: white; padding: 20px; border-radius: 12px;">
    <h6>主教学楼</h6>
    <p>Main Building</p>
</div>
```

---

## 📞 获取帮助

如果在获取图片资源时遇到问题：

1. **版权问题**：确保使用免费可商用图片，或自行创作
2. **技术问题**：使用在线工具处理，无需专业软件
3. **找不到合适图片**：优先使用CSS替代方案
4. **图片质量不佳**：使用AI工具（Midjourney, DALL-E）生成

---

## 📝 更新日志

- **2025-12-31**: 创建图片资源目录结构
- **待完成**: 下载和处理所有图片资源
- **待完成**: 移动端图片压缩优化

---

**注意：** 本文档作为开发参考，实际部署前请确保所有图片资源已合规获取并放置到对应目录。
