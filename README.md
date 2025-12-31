# 🎓 HUST搜题系统

华中科技大学专属题库搜索系统，支持拍照搜题、知识点识别、AI解答。

## 📦 快速开始

### 第一步：安装

双击运行 `首次安装.bat`

> 前提：已安装 Python 3.8+ 并勾选了 "Add Python to PATH"

### 第二步：启动

双击运行 `启动服务器.bat`

浏览器会自动打开 http://localhost:5000

## 📁 目录结构

```
photo-search-questions/
├── 首次安装.bat      # 一键安装脚本
├── 启动服务器.bat    # 一键启动脚本
├── backend/          # 后端代码
├── frontend/         # 前端页面
├── data/             # 数据目录
│   ├── answers/      # 答案文件
│   └── uploads/      # 上传图片
└── photo/            # 题目图片
```

## ✨ 功能特性

- 📷 拍照/上传图片搜题
- 🔍 关键词文本搜索
- 🏷️ 知识点自动识别
- ⭐ 难度评估
- 🤖 AI智能解答
- 📱 移动端适配

## ❓ 常见问题

**Q: 提示"未检测到Python"？**  
A: 请安装 Python 3.8+，安装时务必勾选 "Add Python to PATH"

**Q: 安装依赖失败？**  
A: 检查网络，脚本已使用清华镜像源加速

**Q: 端口被占用？**  
A: 关闭其他占用5000端口的程序，或修改 backend/app_simple.py 中的端口号

## 📝 添加题目

1. 将题目图片放入 `photo/` 目录
2. 在 `data/answers/` 目录创建对应的 `.txt` 答案文件
3. 重启服务器

---

Made with ❤️ for HUST
