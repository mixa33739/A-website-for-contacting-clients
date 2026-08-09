from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models import db, User
from app.utils.validators import validate_email, validate_password

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Регистрация нового пользователя"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Нет данных'}), 400
    
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    # Проверка обязательных полей
    if not name or not email or not password:
        return jsonify({'error': 'Все поля обязательны'}), 400
    
    # Валидация email
    if not validate_email(email):
        return jsonify({'error': 'Некорректный email'}), 400
    
    # Валидация пароля
    password_error = validate_password(password)
    if password_error:
        return jsonify({'error': password_error}), 400
    
    # Проверка существования пользователя
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Пользователь с таким email уже существует'}), 409
    
    # Создание пользователя
    user = User(name=name, email=email, role='user')
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        
        access_token = access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Пользователь успешно зарегистрирован',
            'access_token': access_token,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка при регистрации'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Авторизация пользователя"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Нет данных'}), 400
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email и пароль обязательны'}), 400
    
    # Поиск пользователя
    user = User.query.filter_by(email=email, is_active=True).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Неверный email или пароль'}), 401
    
    # Создание JWT токена
    access_token = access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'message': 'Успешный вход',
        'access_token': access_token,
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role
        }
    }), 200

@auth_bp.route('/me', methods=['GET'], endpoint='get_current_user_info')
@jwt_required()
def get_current_user():
    """Получение данных текущего пользователя"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role
    }), 200
@auth_bp.route('/test', methods=['GET'])
def test_auth():
    return jsonify({'message': 'Auth module works!'})
@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Получение данных текущего пользователя"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role
    }), 200