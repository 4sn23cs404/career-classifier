from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import re
import io

app = Flask(__name__)
CORS(app)

# Career categories with keywords
CAREER_KEYWORDS = {
    'Web Development': {
        'keywords': ['react', 'angular', 'vue', 'html', 'css', 'javascript', 'typescript', 'node', 'express', 'django', 'flask', 'php', 'laravel', 'frontend', 'backend', 'fullstack', 'web', 'bootstrap', 'tailwind', 'nextjs', 'api', 'rest', 'graphql', 'webpack', 'redux', 'sass', 'jquery'],
        'icon': '🌐',
        'color': 'from-blue-500 to-cyan-500'
    },
    'Mobile App Development': {
        'keywords': ['android', 'ios', 'flutter', 'react native', 'swift', 'kotlin', 'mobile', 'app development', 'firebase', 'xamarin', 'dart', 'swiftui', 'jetpack', 'realm', 'sqlite'],
        'icon': '📱',
        'color': 'from-purple-500 to-pink-500'
    },
    'Data Science': {
        'keywords': ['python', 'r', 'machine learning', 'data analysis', 'pandas', 'numpy', 'scikit', 'sklearn', 'tensorflow', 'pytorch', 'keras', 'data science', 'statistics', 'visualization', 'tableau', 'power bi', 'sql', 'mysql', 'postgresql', 'data mining', 'ai', 'artificial intelligence', 'deep learning', 'nlp', 'natural language', 'computer vision', 'jupyter', 'matplotlib', 'seaborn'],
        'icon': '📊',
        'color': 'from-green-500 to-emerald-500'
    },
    'Cloud/DevOps': {
        'keywords': ['aws', 'amazon web services', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'k8s', 'devops', 'ci/cd', 'jenkins', 'terraform', 'ansible', 'cloud', 'linux', 'bash', 'shell', 'git', 'github', 'gitlab', 'github actions', 'microservices', 'nginx', 'apache'],
        'icon': '☁️',
        'color': 'from-orange-500 to-red-500'
    },
    'IoT/Embedded Systems': {
        'keywords': ['iot', 'internet of things', 'embedded', 'arduino', 'raspberry pi', 'sensor', 'mqtt', 'hardware', 'firmware', 'microcontroller', 'esp32', 'esp8266', 'c programming', 'embedded c', 'rtos', 'circuit'],
        'icon': '🔌',
        'color': 'from-indigo-500 to-purple-500'
    },
    'Software Development': {
        'keywords': ['java', 'c++', 'c#', '.net', 'software', 'programming', 'oop', 'object oriented', 'data structures', 'algorithms', 'dsa', 'design patterns', 'testing', 'debugging', 'agile', 'scrum', 'spring', 'hibernate'],
        'icon': '💻',
        'color': 'from-gray-600 to-gray-800'
    }
}

def extract_text_from_pdf(file_stream):
    """Extract text from PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(file_stream)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "
        
        if len(text.strip()) < 50:
            raise ValueError("Could not extract sufficient text from PDF")
        
        return text.lower()
    except Exception as e:
        raise ValueError(f"Error reading PDF: {str(e)}")

def preprocess_text(text):
    """Clean text"""
    text = re.sub(r'[^a-z0-9\s\+\#]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def classify_career(text):
    """Classify career path"""
    text = preprocess_text(text)
    
    if len(text) < 50:
        raise ValueError("Resume text is too short")
    
    category_scores = {}
    matched_keywords_dict = {}
    
    for category, data in CAREER_KEYWORDS.items():
        score = 0
        matched = []
        
        for keyword in data['keywords']:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = re.findall(pattern, text)
            
            if matches:
                count = len(matches)
                score += count
                matched.append({'keyword': keyword, 'count': count})
        
        if score > 0:
            category_scores[category] = score
            matched_keywords_dict[category] = sorted(matched, key=lambda x: x['count'], reverse=True)
    
    if not category_scores:
        raise ValueError("Could not identify technical skills")
    
    total_score = sum(category_scores.values())
    
    results = []
    for category, score in category_scores.items():
        confidence = round((score / total_score) * 100)
        results.append({
            'category': category,
            'confidence': confidence,
            'score': score,
            'matchedKeywords': matched_keywords_dict[category][:8],
            'icon': CAREER_KEYWORDS[category]['icon'],
            'color': CAREER_KEYWORDS[category]['color']
        })
    
    results.sort(key=lambda x: x['score'], reverse=True)
    
    total_confidence = sum(r['confidence'] for r in results[:3])
    if total_confidence != 100 and len(results) > 0:
        results[0]['confidence'] += (100 - total_confidence)
    
    return results[:3]

@app.route('/api/analyze', methods=['POST'])
def analyze_resume():
    """Analyze resume endpoint"""
    try:
        print("Received request to /api/analyze")
        
        if 'file' not in request.files:
            print("No file in request")
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        print(f"File received: {file.filename}")
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Only PDF files supported'}), 400
        
        text = extract_text_from_pdf(io.BytesIO(file.read()))
        print(f"Extracted text length: {len(text)}")
        
        results = classify_career(text)
        print(f"Classification results: {results}")
        
        return jsonify({
            'success': True,
            'results': results,
            'message': 'Resume analyzed successfully'
        })
    
    except ValueError as ve:
        print(f"ValueError: {str(ve)}")
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        print(f"Exception: {str(e)}")
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'CareerClassify API',
        'version': '1.0',
        'endpoints': {
            'POST /api/analyze': 'Analyze resume',
            'GET /api/health': 'Health check'
        }
    })

if __name__ == '__main__':
    print("Starting Flask server...")
    print("Backend will be available at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)