# 📂 数据目录说明

这个目录用于存储题库、答案和上传的图片。

## 📁 目录结构

```
data/
├── question_bank/    # 题库图片目录
├── answers/          # 答案文本目录
└── uploads/          # 临时上传目录
```

## 📚 question_bank/ - 题库图片

### 存放内容
存放所有题目的图片文件

### 命名规范
```
<学科>_<编号>.<扩展名>

示例：
- calculus_001.jpg     (高等数学-第1题)
- physics_002.png      (大学物理-第2题)
- circuit_003.jpg      (电路分析-第3题)
```

### 支持的学科代码

| 代码 | 学科名称 | 示例 |
|------|---------|------|
| `calculus` | 高等数学 | calculus_001.jpg |
| `linear` | 线性代数 | linear_001.jpg |
| `probability` | 概率论 | probability_001.jpg |
| `physics` | 大学物理 | physics_001.jpg |
| `circuit` | 电路分析 | circuit_001.jpg |
| `complex` | 复变函数 | complex_001.jpg |
| `mechanics` | 理论力学 | mechanics_001.jpg |
| `material` | 材料力学 | material_001.jpg |

### 图片要求
- 格式：JPG、PNG、JPEG
- 大小：建议 < 5MB
- 分辨率：推荐 > 800x600
- 内容：清晰、无遮挡、光线充足

## 📝 answers/ - 答案文本

### 存放内容
与题库图片对应的答案文件

### 命名规范
```
<与图片相同的基础名>.txt

示例：
- calculus_001.txt     (对应 calculus_001.jpg)
- physics_002.txt      (对应 physics_002.png)
```

### 答案格式模板

```
题目：[题目完整描述]

解答步骤：
1. [第一步说明]
2. [第二步说明]
3. [第三步说明]
...

答案：[最终答案]

知识点：[学科]-[章节]-[具体知识点]
难度：简单/中等/困难
类型：选择题/计算题/证明题/应用题/综合题/其他
```

### 答案示例

#### 示例1：高等数学
```
题目：求极限 lim(x→0) sin(x)/x

解答步骤：
1. 这是一个 0/0 型未定式
2. 这是重要极限的标准形式
3. 直接应用重要极限公式：lim(x→0) sin(x)/x = 1

答案：1

知识点：高等数学-极限-重要极限
难度：简单
类型：计算题
```

#### 示例2：线性代数
```
题目：设矩阵 A = [[1,2],[3,4]]，求 det(A)

解答步骤：
1. 使用二阶行列式公式：det(A) = ad - bc
2. 代入数值：det(A) = 1×4 - 2×3
3. 计算结果：det(A) = 4 - 6 = -2

答案：-2

知识点：线性代数-行列式-二阶行列式计算
难度：简单
类型：计算题
```

#### 示例3：大学物理
```
题目：一质点做匀加速直线运动，初速度v₀=2m/s，加速度a=3m/s²，求2秒后的速度。

解答步骤：
1. 使用匀变速直线运动速度公式：v = v₀ + at
2. 代入已知量：v = 2 + 3×2
3. 计算：v = 2 + 6 = 8 (m/s)

答案：8 m/s

知识点：大学物理-力学-匀变速直线运动
难度：简单
类型：计算题
```

## 📤 uploads/ - 临时上传

### 用途
存储用户上传的图片（临时文件）

### 特点
- 自动清理（可配置）
- 仅用于临时处理
- 不需要手动管理

### 注意事项
- 此目录内容会被 `.gitignore` 忽略
- 定期清理以节省空间
- 不要存放重要文件

## 🔧 维护建议

### 添加新题目

1. **准备图片**
   ```bash
   # 将图片复制到 question_bank/
   cp 新题目.jpg data/question_bank/calculus_010.jpg
   ```

2. **创建答案**
   ```bash
   # 在 answers/ 创建对应的 .txt 文件
   notepad data/answers/calculus_010.txt
   ```

3. **重启服务器**
   ```bash
   # 题库会自动重新加载
   ```

### 批量导入

使用脚本 `scripts/import_questions.py`：
```bash
python scripts/import_questions.py --source 导入目录/
```

### 备份题库

```powershell
# 压缩备份
Compress-Archive -Path data/ -DestinationPath backup_题库_$(Get-Date -Format 'yyyyMMdd').zip
```

## 📊 统计信息

### 查看题库数量

```powershell
# PowerShell
(Get-ChildItem data\question_bank\*.jpg).Count
```

### 查看各学科题目数

```powershell
Get-ChildItem data\question_bank\ | Group-Object {$_.BaseName.Split('_')[0]} | 
    Select-Object Name, Count | Sort-Object Count -Descending
```

## ⚠️ 注意事项

1. **文件命名**
   - 使用英文和数字
   - 避免特殊字符
   - 保持统一格式

2. **答案质量**
   - 步骤清晰完整
   - 知识点准确
   - 难度评估合理

3. **版权问题**
   - 仅用于个人学习
   - 不要上传侵权内容
   - 尊重原作者权益

4. **数据安全**
   - 定期备份
   - 不要删除原始文件
   - 谨慎操作 uploads/ 目录

## 🎯 题库扩展

### 贡献题库

如果你想分享题目：

1. 遵守命名规范
2. 提供完整答案
3. 标注来源（可选）
4. 提交Pull Request

### 题库模板

可以从 `scripts/create_sample_data.py` 生成示例数据：
```bash
python scripts/create_sample_data.py --count 10 --subject calculus
```

---

**💡 提示**：保持题库整洁有序，方便后续维护和扩展！
