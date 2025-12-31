"""
Flask Web API 服务
提供题目搜索、上传、管理等接口
支持AI实时解答功能
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import traceback

from config import FLASK_CONFIG, UPLOAD_CONFIG, config as ai_config
from database import QuestionDatabase
from ocr_service import get_ocr_service
from matcher import get_matcher
from ai_service import ai_service

# 初始化 Flask 应用
app = Flask(__name__, static_folder='../frontend')
CORS(app)  # 允许跨域请求

# 初始化服务
db = QuestionDatabase()
ocr_service = get_ocr_service()
matcher = get_matcher(db)

# 打印配置状态
ai_config.print_status()


def allowed_file(filename):
    """检查文件类型是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in UPLOAD_CONFIG['allowed_extensions']


@app.route('/')
def index():
    """返回前端页面"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/search', methods=['POST'])
def search_question():
    """
    搜索题目接口（支持AI实时解答）
    
    Request:
        - file: 上传的图片文件
        - use_ai: 是否启用AI解答（当匹配不到时）
        
    Response:
        - results: 匹配结果列表
        - ocr_result: OCR识别结果
        - ai_answer: AI实时解答（如果启用且相似度低）
    """
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件类型'}), 400
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        upload_path = os.path.join(UPLOAD_CONFIG['upload_folder'], filename)
        file.save(upload_path)
        
        # OCR 识别
        ocr_result = ocr_service.recognize_image(upload_path)
        ocr_text = ocr_result['text']
        
        # 题目匹配（使用ML增强）
        matches = matcher.match_question(upload_path, ocr_text, use_ml=True)
        
        # 格式化结果
        results = []
        max_similarity = 0.0
        
        for match in matches:
            question = match['question']
            similarity = match['similarity']
            max_similarity = max(max_similarity, similarity)
            
            # 读取答案
            answer_text = ""
            if question.get('answer_path') and os.path.exists(question['answer_path']):
                try:
                    with open(question['answer_path'], 'r', encoding='utf-8') as f:
                        answer_text = f.read()
                except:
                    answer_text = "[答案文件读取失败]"
            
            results.append({
                'question_id': match['question_id'],
                'similarity': similarity,
                'answer': answer_text,
                'question_image': question['image_path'],
                'category': question.get('category'),
                'confidence': ocr_result.get('confidence', 0),
                'ml_similarity': match.get('ml_similarity'),  # ML增强分数
                'source': 'database'  # 标记来源
            })
        
        # AI解答逻辑：当相似度低于阈值时，调用AI实时解答
        ai_answer = None
        use_ai = request.form.get('use_ai', 'true').lower() == 'true'
        
        if use_ai and ai_config.ENABLE_AI_SOLVER:
            # 判断是否需要AI解答
            need_ai = (
                len(results) == 0 or  # 没有匹配结果
                max_similarity < ai_config.AI_FALLBACK_THRESHOLD  # 相似度太低
            )
            
            if need_ai:
                print(f"🤖 触发AI解答（相似度: {max_similarity:.2f} < 阈值: {ai_config.AI_FALLBACK_THRESHOLD}）")
                
                # 使用豆包+DeepSeek解答
                ai_result = ai_service.solve_with_image(upload_path)
                
                if ai_result['success']:
                    answer_data = ai_result['answer_result']
                    ai_answer = {
                        'answer': answer_data['answer'],
                        'steps': answer_data.get('steps', []),
                        'confidence': answer_data.get('confidence', 0.0),
                        'model': answer_data.get('model', 'deepseek-chat'),
                        'source': 'AI实时解答',
                        'ocr_text': ai_result['ocr_result'].get('text', ocr_text)
                    }
                    
                    # 将AI解答作为第一个结果返回
                    results.insert(0, {
                        'question_id': 'ai_answer',
                        'similarity': 1.0,  # AI解答给最高优先级
                        'answer': ai_answer['answer'],
                        'question_image': None,
                        'category': 'AI解答',
                        'confidence': ai_answer['confidence'],
                        'source': 'ai',
                        'ai_info': ai_answer
                    })
                else:
                    print(f"❌ AI解答失败: {ai_result.get('error')}")
        
        # 返回结果
        return jsonify({
            'success': True,
            'ocr_result': {
                'text': ocr_text,
                'confidence': ocr_result.get('confidence', 0),
                'formulas': ocr_result.get('formulas', []),
            },
            'results': results,
            'total_matches': len(results),
            'max_similarity': max_similarity,
            'ai_enabled': ai_config.ENABLE_AI_SOLVER,
            'ai_triggered': ai_answer is not None,
        })
    
    except Exception as e:
        print(f"搜索错误: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/questions', methods=['GET'])
def list_questions():
    """
    获取题库列表
    
    Query Parameters:
        - category: 类别过滤（可选）
    """
    try:
        category = request.args.get('category')
        
        if category:
            questions = db.search_by_category(category)
        else:
            questions = db.get_all_questions()
        
        # 格式化输出
        result = []
        for q in questions:
            result.append({
                'question_id': q['question_id'],
                'category': q.get('category'),
                'difficulty': q.get('difficulty'),
                'tags': q.get('tags', []),
                'created_at': q.get('created_at'),
            })
        
        return jsonify({
            'success': True,
            'questions': result,
            'total': len(result),
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/question/<question_id>', methods=['GET'])
def get_question(question_id):
    """
    获取单个题目详情
    
    Path Parameters:
        - question_id: 题目ID
    """
    try:
        question = db.get_question_by_id(question_id)
        
        if not question:
            return jsonify({
                'success': False,
                'error': '题目不存在'
            }), 404
        
        # 读取答案
        answer_text = ""
        if question.get('answer_path') and os.path.exists(question['answer_path']):
            with open(question['answer_path'], 'r', encoding='utf-8') as f:
                answer_text = f.read()
        
        return jsonify({
            'success': True,
            'question': {
                'question_id': question['question_id'],
                'image_path': question['image_path'],
                'answer': answer_text,
                'ocr_text': question.get('ocr_text'),
                'category': question.get('category'),
                'difficulty': question.get('difficulty'),
                'tags': question.get('tags', []),
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'services': {
            'database': True,
            'ocr': ocr_service is not None,
            'matcher': matcher is not None,
        }
    })


@app.errorhandler(413)
def request_entity_too_large(error):
    """文件过大错误处理"""
    return jsonify({
        'success': False,
        'error': '文件大小超过限制'
    }), 413


@app.errorhandler(500)
def internal_error(error):
    """内部错误处理"""
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500


if __name__ == '__main__':
    # 确保上传目录存在
    os.makedirs(UPLOAD_CONFIG['upload_folder'], exist_ok=True)
    
    # 启动服务
    app.run(**FLASK_CONFIG)
