# app/routes.py
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

try:
    from app import db
except ImportError:
    from . import db 

from app.models import Document, Comment, Like

main_bp = Blueprint('main', __name__, template_folder='templates')

def allowed_file(filename, allowed_extensions=None):
    if allowed_extensions is None:
        allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'docx', 'zip'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def allowed_image(filename):
    return allowed_file(filename, {'png', 'jpg', 'jpeg', 'gif', 'webp'})

@main_bp.route('/')
def index():
    query = request.args.get('q', '')
    subject = request.args.get('subject', '')
    
    docs_query = Document.query.order_by(Document.upload_date.desc())
    
    if query:
        docs_query = docs_query.filter(
            (Document.title.ilike(f'%{query}%')) | 
            (Document.description.ilike(f'%{query}%'))
        )
        
    if subject:
        docs_query = docs_query.filter(Document.subject == subject)
        
    documents = docs_query.all()
    subjects = db.session.query(Document.subject).distinct().all()
    subjects = [s[0] for s in subjects if s[0]]
    
    return render_template('index.html', documents=documents, query=query, current_subject=subject, subjects=subjects)

@main_bp.route('/document/<int:doc_id>', methods=['GET', 'POST'])
@login_required
def view_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    
    if request.method == 'POST':
        text = request.form.get('comment_text')
        image_file = request.files.get('comment_image')
        
        # Проверка: должен быть хотя бы текст ИЛИ картинка
        if not text and not (image_file and image_file.filename):
            flash('Введите текст или выберите изображение', 'warning')
            return redirect(url_for('main.view_document', doc_id=doc.id))

        new_comment = Comment(text=text, author=current_user, document=doc)
        
        # Обработка картинки комментария
        if image_file and image_file.filename and allowed_image(image_file.filename):
            filename = secure_filename(image_file.filename)
            unique_filename = f"comment_{current_user.id}_{doc_id}_{filename}"
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            image_file.save(save_path)
            new_comment.image_filename = unique_filename
            
        db.session.add(new_comment)
        db.session.commit()
        flash('Комментарий добавлен', 'success')
        return redirect(url_for('main.view_document', doc_id=doc.id))
            
    comments = Comment.query.filter_by(document_id=doc_id).order_by(Comment.timestamp.asc()).all()
    return render_template('view_document.html', doc=doc, comments=comments)

@main_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Функция загрузки нового документа"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        subject = request.form.get('subject')
        
        if 'file' not in request.files:
            flash('Нет файла', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('Файл не выбран', 'danger')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{current_user.id}_{filename}"
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(save_path)
            
            new_doc = Document(
                title=title,
                description=description,
                filename=unique_filename,
                subject=subject or 'Общее',
                author=current_user
            )
            db.session.add(new_doc)
            db.session.commit()
            
            flash('Файл успешно загружен!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Недопустимый тип файла', 'danger')
            
    return render_template('upload.html')

@main_bp.route('/downloads/<filename>')
@login_required
def download_file(filename):
    """Скачивание файла с увеличением счетчика"""
    doc = Document.query.filter_by(filename=filename).first()
    if doc:
        doc.downloads += 1
        db.session.commit()
        
    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, filename, as_attachment=True)

@main_bp.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    """Отображение файлов (картинок документов и комментариев)"""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, filename)

@main_bp.route('/like/<int:doc_id>', methods=['POST'])
@login_required
def toggle_like(doc_id):
    """Логика лайков"""
    doc = Document.query.get_or_404(doc_id)
    existing_like = Like.query.filter_by(user_id=current_user.id, document_id=doc_id).first()
    
    if existing_like:
        db.session.delete(existing_like)
        liked = False
    else:
        new_like = Like(user_id=current_user.id, document_id=doc_id)
        db.session.add(new_like)
        liked = True
    
    db.session.commit()
    return jsonify({'likes': doc.get_likes_count(), 'liked': liked})