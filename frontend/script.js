/**
 * HUST专属搜题系统 - 前端交互脚本
 * 版本: 2.0.0
 * 日期: 2025-12-31
 * 新增功能: 搜索历史、收藏功能、统计面板、快捷键支持
 */

// API 基础URL - 动态获取（支持跨设备访问）
// 如果通过IP访问，则使用当前host；否则使用localhost
const getApiBaseUrl = () => {
    const host = window.location.hostname;
    // 如果是通过IP地址访问，使用相同的host
    if (host !== 'localhost' && host !== '127.0.0.1') {
        return `http://${host}:5000/api`;
    }
    // 默认使用localhost
    return 'http://localhost:5000/api';
};
const API_BASE_URL = getApiBaseUrl();
console.log('[HUST] API Base URL:', API_BASE_URL);

// 全局变量
let selectedFile = null;
let selectedCollege = '';

// 本地存储键名
const STORAGE_KEYS = {
    SEARCH_HISTORY: 'hust_search_history',
    FAVORITES: 'hust_favorites',
    STATS: 'hust_stats',
    NIGHT_MODE: 'hust_night_mode'
};

// DOM 元素
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const searchBtn = document.getElementById('searchBtn');
const previewImage = document.getElementById('previewImage');
const progressArea = document.getElementById('progressArea');
const resultsArea = document.getElementById('resultsArea');
const ocrResultCard = document.getElementById('ocrResultCard');
const ocrText = document.getElementById('ocrText');
const ocrConfidence = document.getElementById('ocrConfidence');
const collegeSelect = document.getElementById('collegeSelect');

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    initKeyboardShortcuts();
    loadSearchHistory();
    updateStatsPanel();
    restoreNightMode();
    console.log('[HUST] 系统初始化完成 v2.0');
});

// 初始化事件监听
function initEventListeners() {
    // 上传按钮点击
    uploadBtn.addEventListener('click', () => {
        fileInput.click();
    });
    
    // 文件选择
    fileInput.addEventListener('change', handleFileSelect);
    
    // 学院选择
    collegeSelect.addEventListener('change', (e) => {
        selectedCollege = e.target.value;
        console.log('[HUST] 选择学院:', selectedCollege || '全部');
    });
    
    // 拖拽上传
    uploadArea.addEventListener('click', () => {
        if (!selectedFile) {
            fileInput.click();
        }
    });
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
    
    // 搜索按钮
    searchBtn.addEventListener('click', performSearch);
    
    // 题库浏览按钮
    document.getElementById('questionBankBtn')?.addEventListener('click', (e) => {
        e.preventDefault();
        alert('题库浏览功能开发中，敬请期待！');
    });
    
    // 夜间模式按钮
    document.getElementById('nightModeBtn')?.addEventListener('click', toggleNightMode);
}

// 处理文件选择
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

// 处理文件
function handleFile(file) {
    // 验证文件类型
    const validTypes = ['image/jpeg', 'image/png', 'image/bmp', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
        showAlert('请上传图片文件 (JPG, PNG, BMP, GIF)', 'warning');
        return;
    }
    
    // 验证文件大小 (10MB)
    if (file.size > 10 * 1024 * 1024) {
        showAlert('图片大小不能超过10MB', 'warning');
        return;
    }
    
    selectedFile = file;
    console.log('[HUST] 文件已选择:', file.name, formatFileSize(file.size));
    
    // 显示预览
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImage.src = e.target.result;
        previewImage.classList.remove('d-none');
        document.querySelector('.upload-placeholder').style.display = 'none';
    };
    reader.readAsDataURL(file);
    
    // 启用搜索按钮
    searchBtn.disabled = false;
}

// 执行搜索
async function performSearch() {
    if (!selectedFile) {
        showAlert('请先上传图片', 'warning');
        return;
    }
    
    console.log('[HUST] 开始搜题，学院筛选:', selectedCollege || '全部');
    
    // 获取AI开关状态
    const enableAI = document.getElementById('enableAI')?.checked ?? true;
    console.log('[HUST] AI解答:', enableAI ? '已启用' : '已禁用');
    
    // 显示进度
    progressArea.classList.remove('d-none');
    searchBtn.disabled = true;
    resultsArea.innerHTML = ''; // 优化：移除loading spinner
    
    try {
        // 创建 FormData
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('college', selectedCollege); // 添加学院参数
        formData.append('use_ai', enableAI ? 'true' : 'false');  // 添加AI开关
        
        // 发送请求
        const startTime = Date.now();
        const response = await fetch(`${API_BASE_URL}/search`, {
            method: 'POST',
            body: formData
        });
        
        const elapsed = Date.now() - startTime;
        console.log(`[HUST] 搜索完成，耗时: ${elapsed}ms`);
        
        if (!response.ok) {
            throw new Error(`搜索失败 (${response.status})`);
        }
        
        const data = await response.json();
        
        // 隐藏进度
        progressArea.classList.add('d-none');
        searchBtn.disabled = false;
        
        if (data.success) {
            // 保存OCR结果供后续AI使用
            window.lastOcrResult = data.ocr_result;
            window.lastKnowledgeTags = data.knowledge_tags;
            window.lastQuestionType = data.question_type;
            
            // 显示OCR结果
            displayOCRResult(data.ocr_result);
            
            // 显示搜索结果（优先题库匹配）
            displayResults(data.results, false);
            
            // 添加搜索历史
            addSearchHistory({
                preview: selectedFile.name,
                resultsCount: data.results.length,
                college: selectedCollege
            });
            
            console.log('[HUST] 结果显示完成，共', data.results.length, '条题库匹配');
        } else {
            throw new Error(data.error || '搜索失败');
        }
        
    } catch (error) {
        console.error('[HUST] 搜索错误:', error);
        progressArea.classList.add('d-none');
        searchBtn.disabled = false;
        
        resultsArea.innerHTML = `
            <div class="alert alert-danger">
                <strong>❌ 搜索失败!</strong><br>
                ${error.message}<br>
                <small class="text-muted mt-2 d-block">
                    请检查网络连接或联系系统管理员
                </small>
            </div>
        `;
    }
}

// 显示OCR结果
function displayOCRResult(ocrResult) {
    ocrResultCard.classList.remove('d-none');
    
    const ocrTextElement = document.getElementById('ocrText');
    const ocrTextContent = ocrResult.text || '[未识别到文字]';
    
    console.log('[HUST] OCR识别文本:', ocrTextContent.substring(0, 50) + '...');
    
    // 优化：使用innerHTML以支持LaTeX渲染，但先转义HTML防止XSS
    const formattedText = escapeHtml(ocrTextContent).replace(/\n/g, '<br>');
    ocrTextElement.innerHTML = formattedText;
    
    // 渲染OCR文本中的LaTeX（如果有）
    renderMathAndMarkdown(ocrTextElement);
    
    const confidence = Math.round(ocrResult.confidence * 100);
    ocrConfidence.textContent = `${confidence}%`;
    ocrConfidence.className = 'badge ' + (
        confidence > 80 ? 'bg-success' : 
        confidence > 60 ? 'bg-warning' : 
        'bg-danger'
    );
    
    // 显示知识点标签
    if (ocrResult.knowledge_tags && ocrResult.knowledge_tags.length > 0) {
        let tagsHtml = '<div class="mt-2"><strong>🏷️ 识别到的知识点：</strong><br>';
        ocrResult.knowledge_tags.forEach(tag => {
            tagsHtml += `<span class="badge me-1 mt-1" style="background-color: ${tag.color};">${tag.name}</span>`;
        });
        tagsHtml += '</div>';
        ocrTextElement.innerHTML += tagsHtml;
    }
    
    // 显示题目类型
    if (ocrResult.question_type) {
        ocrTextElement.innerHTML += `<div class="mt-2"><small class="text-muted">📋 题目类型：${ocrResult.question_type}</small></div>`;
    }
}

// 显示搜索结果
function displayResults(results, aiTriggered = false) {
    // 先显示AI解答按钮区域
    let aiButtonHtml = `
        <div class="ai-answer-section mb-3" id="aiAnswerSection">
            <div class="card border-primary">
                <div class="card-body text-center py-3">
                    <h6 class="mb-2">🤖 需要AI智能解答？</h6>
                    <p class="text-muted small mb-2">题库匹配结果不满意？点击下方按钮获取DeepSeek AI实时解答</p>
                    <button class="btn btn-primary btn-lg" onclick="requestAIAnswer()" id="aiAnswerBtn">
                        <span class="spinner-border spinner-border-sm d-none" id="aiSpinner"></span>
                        🚀 使用AI解答
                    </button>
                </div>
            </div>
        </div>
        <div id="aiResultContainer"></div>
    `;
    
    if (results.length === 0) {
        resultsArea.innerHTML = aiButtonHtml + `
            <div class="no-results">
                <svg width="80" height="80" fill="currentColor" class="bi bi-inbox" viewBox="0 0 16 16">
                    <path d="M4.98 4a.5.5 0 0 0-.39.188L1.54 8H6a.5.5 0 0 1 .5.5 1.5 1.5 0 1 0 3 0A.5.5 0 0 1 10 8h4.46l-3.05-3.812A.5.5 0 0 0 11.02 4H4.98zm9.954 5H10.45a2.5 2.5 0 0 1-4.9 0H1.066l.32 2.562a.5.5 0 0 0 .497.438h12.234a.5.5 0 0 0 .496-.438L14.933 9zM3.809 3.563A1.5 1.5 0 0 1 4.981 3h6.038a1.5 1.5 0 0 1 1.172.563l3.7 4.625a.5.5 0 0 1 .105.374l-.39 3.124A1.5 1.5 0 0 1 14.117 13H1.883a1.5 1.5 0 0 1-1.489-1.314l-.39-3.124a.5.5 0 0 1 .106-.374l3.7-4.625z"/>
                </svg>
                <p class="mt-3 fw-bold text-hust-blue">题库中未找到匹配的题目</p>
                <p class="text-muted">
                    您可以：<br>
                    • 点击上方"使用AI解答"获取智能解答<br>
                    • 尝试更换图片或调整拍摄角度<br>
                    • <a href="#" class="text-hust-red">提交此题目</a>帮助完善题库
                </p>
            </div>
        `;
        return;
    }
    
    let html = aiButtonHtml + '<div class="results-container"><h5 class="mb-3">📚 题库匹配结果</h5>';
    
    results.forEach((result, index) => {
        const similarity = Math.round(result.similarity * 100);
        const badgeClass = similarity > 90 ? 'bg-success' : 
                          similarity > 75 ? 'bg-primary' : 
                          'bg-warning';
        
        // 判断是否为华科专属解析
        const isHustExclusive = result.source === 'database' && similarity >= 80;
        const isAIAnswer = result.source === 'ai';
        
        // 处理答案文本 - 直接使用，不进行Base64编码
        const answerText = result.answer || '[暂无答案]';
        const answerId = `answer-${index}`;
        
        // 处理类别显示
        let categoryBadge = '';
        if (result.category) {
            const categoryColor = isHustExclusive ? 'bg-hust-blue' : (isAIAnswer ? 'bg-success' : 'bg-secondary');
            categoryBadge = `<span class="badge ${categoryColor} me-2">${result.category}</span>`;
        }
        
        // AI模型标识
        let aiModelBadge = '';
        if (isAIAnswer && result.ai_model) {
            aiModelBadge = `<span class="badge bg-gradient" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                ${result.ai_model} AI
            </span>`;
        }
        
        // 难度标识
        let difficultyBadge = '';
        if (result.difficulty) {
            const stars = '⭐'.repeat(result.difficulty.stars);
            difficultyBadge = `<span class="badge ms-1" style="background-color: ${result.difficulty.color};">${result.difficulty.level} ${stars}</span>`;
        }
        
        // 知识点标签
        let knowledgeTagsHtml = '';
        if (result.knowledge_tags && result.knowledge_tags.length > 0) {
            knowledgeTagsHtml = '<div class="mt-2">';
            result.knowledge_tags.forEach(tag => {
                knowledgeTagsHtml += `<span class="badge me-1" style="background-color: ${tag.color}; font-size: 11px;">${tag.name}</span>`;
            });
            knowledgeTagsHtml += '</div>';
        }
        
        html += `
            <div class="result-item ${isAIAnswer ? 'ai-answer-item' : ''}">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div>
                        <h6 class="mb-1 fw-bold" style="color: ${isAIAnswer ? '#667eea' : 'var(--hust-blue)'};">
                            ${isAIAnswer ? '🤖 AI实时解答' : '📚 题目 #' + result.question_id}
                            ${isHustExclusive ? '<span class="hust-exclusive-badge">华科专属</span>' : ''}
                        </h6>
                        ${categoryBadge}
                        ${aiModelBadge}
                        ${difficultyBadge}
                        ${result.ml_similarity ? `<span class="badge bg-info">ML增强匹配</span>` : ''}
                        ${knowledgeTagsHtml}
                    </div>
                    <span class="similarity-badge ${badgeClass}">
                        相似度: ${similarity}%
                    </span>
                </div>
                
                ${isHustExclusive ? `
                <div class="alert alert-success py-2 px-3 mb-2" role="alert">
                    <small>
                        ✅ <strong>华科校内解析</strong> - 优先展示
                        ${result.confidence ? ` · 置信度: ${Math.round(result.confidence * 100)}%` : ''}
                    </small>
                </div>` : ''}
                
                ${!isAIAnswer && result.image_url ? `
                <div class="question-image-section mt-2 mb-3">
                    <strong class="text-muted">📷 题目原图：</strong>
                    <div class="question-image-container mt-2">
                        <img src="${result.image_url}" 
                             alt="题目图片" 
                             class="question-thumbnail"
                             onclick="showFullImage('${result.image_url}', '${result.question_id}')"
                             title="点击查看大图">
                        <div class="image-overlay">
                            <span>🔍 点击放大</span>
                        </div>
                    </div>
                </div>` : ''}
                
                <div class="answer-section mt-3">
                    <strong class="text-hust-blue">📖 详细解答：</strong>
                    <div class="answer-content mt-2" id="${answerId}"></div>
                </div>
                
                ${!isAIAnswer ? `
                <div class="mt-3 d-flex gap-2">
                    <button class="btn btn-sm btn-outline-primary" onclick="collectQuestion(${index})">
                        ⭐ 收藏
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="reportQuestion(${index})">
                        🚩 纠错
                    </button>
                </div>` : ''}
            </div>
        `;
    });
    
    html += '</div>';
    
    resultsArea.innerHTML = html;
    
    // 渲染LaTeX和Markdown - 直接从result对象获取答案
    results.forEach((result, index) => {
        const answerId = `answer-${index}`;
        const element = document.getElementById(answerId);
        if (element && result.answer) {
            // 直接设置纯文本内容
            element.textContent = result.answer;
            // 渲染
            renderMathAndMarkdown(element);
        }
    });
    
    console.log('[HUST] 结果渲染完成');
}

// 请求AI解答
async function requestAIAnswer() {
    const btn = document.getElementById('aiAnswerBtn');
    const spinner = document.getElementById('aiSpinner');
    const container = document.getElementById('aiResultContainer');
    
    if (!window.lastOcrResult || !window.lastOcrResult.text) {
        showAlert('请先上传图片并搜索', 'warning');
        return;
    }
    
    // 显示加载状态
    btn.disabled = true;
    spinner.classList.remove('d-none');
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> AI正在思考中...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/ai_answer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: window.lastOcrResult.text,
                subject: window.lastKnowledgeTags?.[0]?.name || '高等数学',
                question_type: window.lastQuestionType || '综合类'
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.ai_answer) {
            // 显示AI解答
            displayAIResult(data.ai_answer);
            
            // 更新按钮状态
            btn.innerHTML = '✅ AI解答已生成';
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-success');
            
            console.log('[HUST] AI解答生成成功');
        } else {
            throw new Error(data.error || 'AI解答生成失败');
        }
        
    } catch (error) {
        console.error('[HUST] AI解答错误:', error);
        btn.disabled = false;
        btn.innerHTML = '🚀 重试AI解答';
        showAlert('AI解答失败: ' + error.message, 'danger');
    }
}

// 显示AI解答结果
function displayAIResult(aiAnswer) {
    const container = document.getElementById('aiResultContainer');
    
    const html = `
        <div class="result-item ai-answer-item" style="border: 2px solid #667eea; background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf2 100%);">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <div>
                    <h6 class="mb-1 fw-bold" style="color: #667eea;">
                        🤖 DeepSeek AI 实时解答
                    </h6>
                    <span class="badge bg-gradient" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                        ${aiAnswer.ai_model || 'DeepSeek'} AI
                    </span>
                    <span class="badge bg-success ms-1">实时生成</span>
                </div>
                <span class="similarity-badge bg-info">
                    AI置信度: ${Math.round((aiAnswer.confidence || 0.98) * 100)}%
                </span>
            </div>
            
            <div class="answer-section mt-3">
                <strong class="text-primary">📖 AI详细解答：</strong>
                <div class="answer-content mt-2" id="ai-answer-content">
                    ${aiAnswer.answer || '[暂无答案]'}
                </div>
            </div>
            
            <div class="mt-3 text-muted small">
                💡 提示：AI解答仅供参考，建议结合教材和标准答案学习
            </div>
        </div>
    `;
    
    container.innerHTML = html;
    
    // 渲染LaTeX
    const element = document.getElementById('ai-answer-content');
    if (element) {
        renderMathAndMarkdown(element);
    }
    
    // 滚动到AI解答位置
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// LaTeX和Markdown渲染函数 - 简洁高效版
function renderMathAndMarkdown(element) {
    if (!element) return;
    
    let content = element.textContent || '';
    console.log('[HUST] 开始渲染，内容长度:', content.length);
    
    // 检测是否为Markdown格式
    const hasMarkdown = /^##\s/.test(content.trim()) || content.includes('\n##') || content.includes('**');
    
    if (hasMarkdown) {
        // Markdown格式：先渲染Markdown，再渲染LaTeX
        if (typeof marked !== 'undefined') {
            try {
                // 直接使用marked渲染，不需要保护LaTeX（marked会保留$符号）
                const html = marked.parse(content, {
                    breaks: true,
                    gfm: true
                });
                element.innerHTML = html;
                console.log('[HUST] Markdown渲染完成');
            } catch (error) {
                console.error('[HUST] Markdown错误:', error);
                element.innerHTML = content.replace(/\n/g, '<br>');
            }
        } else {
            element.innerHTML = content.replace(/\n/g, '<br>');
        }
    } else {
        // 纯文本：直接显示
        element.innerHTML = content.replace(/\n/g, '<br>');
    }
    
    // 渲染LaTeX公式（使用KaTeX）
    setTimeout(() => {
        if (typeof renderMathInElement !== 'undefined') {
            try {
                console.log('[HUST] 开始KaTeX渲染...');
                renderMathInElement(element, {
                    delimiters: [
                        {left: '$$', right: '$$', display: true},
                        {left: '$', right: '$', display: false}
                    ],
                    throwOnError: false,
                    strict: false
                });
                console.log('[HUST] ✅ KaTeX渲染成功');
            } catch (error) {
                console.error('[HUST] KaTeX错误:', error);
            }
        } else {
            console.error('[HUST] ❌ KaTeX未加载');
        }
    }, 50);
}

// HTML转义函数，防止XSS，但保留LaTeX公式符号
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 显示完整图片（模态框）
function showFullImage(imageUrl, questionId) {
    // 创建模态框
    const modal = document.createElement('div');
    modal.className = 'image-modal';
    modal.innerHTML = `
        <div class="image-modal-content">
            <div class="image-modal-header">
                <span>📷 题目 #${questionId}</span>
                <button class="image-modal-close" onclick="closeImageModal()">&times;</button>
            </div>
            <div class="image-modal-body">
                <img src="${imageUrl}" alt="题目图片" class="full-image">
            </div>
            <div class="image-modal-footer">
                <button class="btn btn-sm btn-outline-primary" onclick="downloadImage('${imageUrl}', '${questionId}')">
                    ⬇️ 下载图片
                </button>
                <button class="btn btn-sm btn-secondary" onclick="closeImageModal()">
                    关闭
                </button>
            </div>
        </div>
    `;
    
    // 点击背景关闭
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeImageModal();
        }
    });
    
    document.body.appendChild(modal);
    document.body.style.overflow = 'hidden';
    
    // ESC键关闭
    document.addEventListener('keydown', handleEscKey);
}

// 关闭图片模态框
function closeImageModal() {
    const modal = document.querySelector('.image-modal');
    if (modal) {
        modal.remove();
        document.body.style.overflow = '';
        document.removeEventListener('keydown', handleEscKey);
    }
}

// ESC键处理
function handleEscKey(e) {
    if (e.key === 'Escape') {
        closeImageModal();
    }
}

// 下载图片
function downloadImage(imageUrl, questionId) {
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `${questionId}.jpg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showAlert('图片下载中...', 'info');
}

// 收藏题目
function collectQuestion(index, questionData = null) {
    const favorites = getFavorites();
    const questionId = questionData?.question_id || `question_${index}`;
    
    // 检查是否已收藏
    const existingIndex = favorites.findIndex(f => f.question_id === questionId);
    
    if (existingIndex >= 0) {
        // 取消收藏
        favorites.splice(existingIndex, 1);
        localStorage.setItem(STORAGE_KEYS.FAVORITES, JSON.stringify(favorites));
        showAlert('已取消收藏', 'warning');
        updateFavoriteButton(index, false);
    } else {
        // 添加收藏
        const newFavorite = {
            question_id: questionId,
            timestamp: Date.now(),
            answer: questionData?.answer || '',
            category: questionData?.category || '未分类'
        };
        favorites.push(newFavorite);
        localStorage.setItem(STORAGE_KEYS.FAVORITES, JSON.stringify(favorites));
        showAlert('⭐ 已收藏到本地', 'success');
        updateFavoriteButton(index, true);
    }
    
    updateStatsPanel();
}

// 更新收藏按钮状态
function updateFavoriteButton(index, isFavorited) {
    const btn = document.querySelector(`[onclick="collectQuestion(${index})"]`);
    if (btn) {
        btn.innerHTML = isFavorited ? '💛 已收藏' : '⭐ 收藏';
        btn.classList.toggle('btn-warning', isFavorited);
        btn.classList.toggle('btn-outline-primary', !isFavorited);
    }
}

// 获取收藏列表
function getFavorites() {
    try {
        return JSON.parse(localStorage.getItem(STORAGE_KEYS.FAVORITES) || '[]');
    } catch {
        return [];
    }
}

// 获取搜索历史
function getSearchHistory() {
    try {
        return JSON.parse(localStorage.getItem(STORAGE_KEYS.SEARCH_HISTORY) || '[]');
    } catch {
        return [];
    }
}

// 添加搜索历史
function addSearchHistory(searchData) {
    const history = getSearchHistory();
    const newEntry = {
        id: Date.now(),
        timestamp: Date.now(),
        preview: searchData.preview || '',
        resultsCount: searchData.resultsCount || 0,
        college: searchData.college || ''
    };
    
    // 最多保留20条历史
    history.unshift(newEntry);
    if (history.length > 20) {
        history.pop();
    }
    
    localStorage.setItem(STORAGE_KEYS.SEARCH_HISTORY, JSON.stringify(history));
    
    // 更新统计
    updateStats('searchCount');
    updateStatsPanel();
    loadSearchHistory();
}

// 加载搜索历史到UI
function loadSearchHistory() {
    const historyContainer = document.getElementById('searchHistoryList');
    if (!historyContainer) return;
    
    const history = getSearchHistory();
    
    if (history.length === 0) {
        historyContainer.innerHTML = '<div class="text-muted text-center py-3">暂无搜索历史</div>';
        return;
    }
    
    let html = '';
    history.slice(0, 5).forEach((item, index) => {
        const timeStr = formatTimeAgo(item.timestamp);
        html += `
            <div class="history-item d-flex justify-content-between align-items-center py-2 border-bottom">
                <div>
                    <small class="text-muted">${timeStr}</small>
                    <div class="small">${item.resultsCount} 个结果 ${item.college ? '· ' + item.college : ''}</div>
                </div>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteHistoryItem(${item.id})" title="删除">
                    ✕
                </button>
            </div>
        `;
    });
    
    historyContainer.innerHTML = html;
}

// 删除历史记录
function deleteHistoryItem(id) {
    let history = getSearchHistory();
    history = history.filter(h => h.id !== id);
    localStorage.setItem(STORAGE_KEYS.SEARCH_HISTORY, JSON.stringify(history));
    loadSearchHistory();
    showAlert('已删除', 'info');
}

// 清空搜索历史
function clearSearchHistory() {
    if (confirm('确定要清空所有搜索历史吗？')) {
        localStorage.setItem(STORAGE_KEYS.SEARCH_HISTORY, '[]');
        loadSearchHistory();
        showAlert('搜索历史已清空', 'success');
    }
}

// 更新统计数据
function updateStats(key) {
    const stats = getStats();
    stats[key] = (stats[key] || 0) + 1;
    stats.lastSearchTime = Date.now();
    localStorage.setItem(STORAGE_KEYS.STATS, JSON.stringify(stats));
}

// 获取统计数据
function getStats() {
    try {
        return JSON.parse(localStorage.getItem(STORAGE_KEYS.STATS) || '{}');
    } catch {
        return {};
    }
}

// 更新统计面板
function updateStatsPanel() {
    const stats = getStats();
    const favorites = getFavorites();
    const history = getSearchHistory();
    
    // 更新各个统计数字
    const searchCountEl = document.getElementById('statSearchCount');
    const favoriteCountEl = document.getElementById('statFavoriteCount');
    const historyCountEl = document.getElementById('statHistoryCount');
    
    if (searchCountEl) searchCountEl.textContent = stats.searchCount || 0;
    if (favoriteCountEl) favoriteCountEl.textContent = favorites.length;
    if (historyCountEl) historyCountEl.textContent = history.length;
}

// 格式化时间
function formatTimeAgo(timestamp) {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);
    
    if (seconds < 60) return '刚刚';
    if (seconds < 3600) return Math.floor(seconds / 60) + ' 分钟前';
    if (seconds < 86400) return Math.floor(seconds / 3600) + ' 小时前';
    if (seconds < 604800) return Math.floor(seconds / 86400) + ' 天前';
    
    const date = new Date(timestamp);
    return `${date.getMonth() + 1}/${date.getDate()}`;
}

// 键盘快捷键支持
function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Enter 键搜题（当没有在输入框中时）
        if (e.key === 'Enter' && !e.target.matches('input, textarea')) {
            e.preventDefault();
            if (!searchBtn.disabled) {
                searchBtn.click();
            }
        }
        
        // Ctrl/Cmd + U 上传图片
        if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
            e.preventDefault();
            fileInput.click();
        }
        
        // Ctrl/Cmd + D 切换夜间模式
        if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
            e.preventDefault();
            toggleNightMode();
        }
        
        // Escape 清除预览
        if (e.key === 'Escape' && selectedFile) {
            clearPreview();
        }
    });
    
    console.log('[HUST] 快捷键已初始化 (Enter=搜索, Ctrl+U=上传, Ctrl+D=夜间模式, Esc=清除)');
}

// 清除预览
function clearPreview() {
    selectedFile = null;
    previewImage.classList.add('d-none');
    document.querySelector('.upload-placeholder').style.display = 'block';
    searchBtn.disabled = true;
    fileInput.value = '';
    showAlert('已清除图片', 'info');
}

// 恢复夜间模式
function restoreNightMode() {
    if (localStorage.getItem(STORAGE_KEYS.NIGHT_MODE) === 'true') {
        document.body.classList.add('dark-mode');
        const nightModeBtn = document.getElementById('nightModeBtn');
        if (nightModeBtn) {
            nightModeBtn.innerHTML = '☀️';
            nightModeBtn.title = '切换日间模式';
        }
    }
}

// 举报题目
function reportQuestion(index) {
    console.log('[HUST] 举报题目:', index);
    showAlert('感谢您的反馈！我们会尽快处理', 'info');
}

// 夜间模式切换
function toggleNightMode() {
    const isDark = document.body.classList.toggle('dark-mode');
    localStorage.setItem(STORAGE_KEYS.NIGHT_MODE, isDark ? 'true' : 'false');
    
    // 更新按钮图标
    const nightModeBtn = document.getElementById('nightModeBtn');
    if (nightModeBtn) {
        nightModeBtn.innerHTML = isDark ? '☀️' : '🌙';
        nightModeBtn.title = isDark ? '切换日间模式' : '切换夜间模式';
    }
    
    console.log('[HUST] 夜间模式:', isDark ? '开启' : '关闭');
    showAlert(isDark ? '🌙 夜间模式已开启 - 保护您的眼睛' : '☀️ 日间模式已开启', 'info');
}

// 显示提示信息
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed animate__animated animate__fadeInRight`;
    alertDiv.style.cssText = 'top: 80px; right: 20px; z-index: 9999; min-width: 300px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    // 3秒后自动关闭
    setTimeout(() => {
        alertDiv.classList.add('animate__fadeOutRight');
        setTimeout(() => alertDiv.remove(), 300);
    }, 3000);
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

// 显示收藏列表
function showFavorites() {
    const favorites = getFavorites();
    
    if (favorites.length === 0) {
        showAlert('暂无收藏的题目', 'info');
        return;
    }
    
    let html = '<div class="favorites-list">';
    favorites.forEach((fav, index) => {
        const timeStr = formatTimeAgo(fav.timestamp);
        html += `
            <div class="favorite-item p-3 border-bottom">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>${fav.question_id}</strong>
                        <span class="badge bg-secondary ms-2">${fav.category}</span>
                    </div>
                    <small class="text-muted">${timeStr}</small>
                </div>
                <div class="small text-muted mt-1">${(fav.answer || '').substring(0, 100)}...</div>
                <button class="btn btn-sm btn-outline-danger mt-2" onclick="removeFavorite('${fav.question_id}')">
                    删除
                </button>
            </div>
        `;
    });
    html += '</div>';
    
    // 显示模态框
    showModal('我的收藏 (' + favorites.length + ')', html);
}

// 删除收藏
function removeFavorite(questionId) {
    let favorites = getFavorites();
    favorites = favorites.filter(f => f.question_id !== questionId);
    localStorage.setItem(STORAGE_KEYS.FAVORITES, JSON.stringify(favorites));
    updateStatsPanel();
    showFavorites(); // 刷新列表
    showAlert('已取消收藏', 'warning');
}

// 显示模态框
function showModal(title, content) {
    // 移除现有模态框
    const existingModal = document.getElementById('dynamicModal');
    if (existingModal) existingModal.remove();
    
    const modalHtml = `
        <div class="modal fade" id="dynamicModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body" style="max-height: 60vh; overflow-y: auto;">
                        ${content}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('dynamicModal'));
    modal.show();
}

// 显示快捷键帮助
function showShortcutsHelp() {
    const content = `
        <table class="table">
            <thead>
                <tr>
                    <th>快捷键</th>
                    <th>功能</th>
                </tr>
            </thead>
            <tbody>
                <tr><td><kbd>Enter</kbd></td><td>开始搜题</td></tr>
                <tr><td><kbd>Ctrl</kbd> + <kbd>U</kbd></td><td>上传图片</td></tr>
                <tr><td><kbd>Ctrl</kbd> + <kbd>D</kbd></td><td>切换夜间模式</td></tr>
                <tr><td><kbd>Esc</kbd></td><td>清除当前图片</td></tr>
            </tbody>
        </table>
        <p class="text-muted small">💡 提示：在Mac上使用 <kbd>Cmd</kbd> 代替 <kbd>Ctrl</kbd></p>
    `;
    showModal('⌨️ 快捷键', content);
}

console.log('[HUST] HUST专属搜题系统 v2.0.0 加载完成');
