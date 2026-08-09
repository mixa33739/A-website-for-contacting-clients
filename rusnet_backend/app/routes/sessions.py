from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, UserSession, User
from datetime import datetime

sessions_bp = Blueprint('sessions', __name__, url_prefix='/api/sessions')

@sessions_bp.route('', methods=['POST'])
@jwt_required()
def create_session():
    """Создание записи о сессии пользователя"""
    try:
        user_id = get_jwt_identity()
        
        # Получаем информацию о запросе
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        
        # Создаем запись о сессии
        session = UserSession(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            login_time=datetime.utcnow()
        )
        
        db.session.add(session)
        db.session.commit()
        
        return {'message': 'Сессия создана', 'session_id': session.id}, 201
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500

@sessions_bp.route('/my', methods=['GET'])
@jwt_required()
def get_my_sessions():
    """Получение активных сессий текущего пользователя"""
    try:
        user_id = get_jwt_identity()
        sessions = UserSession.query.filter_by(user_id=user_id, is_active=True).all()
        
        sessions_data = []
        for session in sessions:
            sessions_data.append({
                'id': session.id,
                'ip_address': session.ip_address,
                'user_agent': session.user_agent,
                'login_time': session.login_time.isoformat(),
                'last_activity': session.last_activity.isoformat() if session.last_activity else None
            })
        
        return {'sessions': sessions_data}, 200
    except Exception as e:
        return {'error': str(e)}, 500