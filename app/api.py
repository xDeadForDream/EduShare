from flask import Blueprint, jsonify
from app.quotes import get_random_quote

api_bp = Blueprint('api', __name__)

@api_bp.route('/documents', methods=['GET'])
def get_documents():
    from app.models import Document
    docs = Document.query.all()
    result = []
    for doc in docs:
        result.append({
            'id': doc.id,
            'title': doc.title,
            'author': doc.author.username,
            'date': doc.upload_date.strftime('%Y-%m-%d')
        })
    return jsonify(result)

@api_bp.route('/quote', methods=['GET'])
def get_quote():
    # Возвращаем случайную русскую цитату
    return jsonify(get_random_quote())