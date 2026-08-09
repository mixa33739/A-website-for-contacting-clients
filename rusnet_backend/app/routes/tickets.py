from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Ticket, TicketStatus, Site, User
from datetime import datetime
from sqlalchemy import or_
from datetime import datetime, timezone

tickets_bp = Blueprint('tickets', __name__, url_prefix='/api/tickets')

@tickets_bp.route('', methods=['GET'])
@jwt_required()
def get_tickets():
    """Получение списка обращений"""
    try:
        # ИСПРАВЛЕНО: преобразуем строку в число
        current_user_id = int(get_jwt_identity())
        
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        # Получаем параметры из query string
        status = request.args.get('status')
        priority = request.args.get('priority')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Базовый запрос
        query = Ticket.query
        
        # Если не админ, показываем только свои обращения
        if user.role != 'admin':
            query = query.filter_by(user_id=current_user_id)
        
        # Применение фильтров
        if status:
            query = query.join(TicketStatus).filter(TicketStatus.name == status)
        
        if priority:
            query = query.filter_by(priority=priority)
        
        # Сортировка по дате создания (новые первыми)
        query = query.order_by(Ticket.created_at.desc())
        
        # Пагинация
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        tickets_data = []
        for ticket in pagination.items:
            tickets_data.append({
                'id': ticket.id,
                'subject': ticket.subject,
                'description': ticket.description,
                'priority': ticket.priority,
               'created_at': ticket.created_at.replace(tzinfo=timezone.utc).astimezone().isoformat(),
                'updated_at': ticket.updated_at.isoformat(),
                'status': {
                    'id': ticket.status.id,
                    'name': ticket.status.name,
                    'color': ticket.status.color_code
                },
                'site': {
                    'id': ticket.site.id,
                    'name': ticket.site.name
                },
                'author': {
                    'id': ticket.author.id,
                    'name': ticket.author.name
                }
            })
        
        return jsonify({
            'tickets': tickets_data,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        print(f"ERROR in get_tickets: {str(e)}")  # ← Для отладки
        return jsonify({'error': f'Ошибка при получении обращений: {str(e)}'}), 500

@tickets_bp.route('', methods=['POST'])
@jwt_required()
def create_ticket():
    """Создание нового обращения"""
    try:
        # ИСПРАВЛЕНО: преобразуем строку в число
        current_user_id = int(get_jwt_identity())
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Нет данных'}), 400
        
        subject = data.get('subject', '').strip()
        description = data.get('description', '').strip()
        site_id = data.get('site_id')
        priority = data.get('priority', 'medium')
        
        # Валидация
        if not subject or not description or not site_id:
            return jsonify({'error': 'Все обязательные поля должны быть заполнены'}), 400
        
        if len(subject) > 200:
            return jsonify({'error': 'Тема слишком длинная (максимум 200 символов)'}), 400
        
        if priority not in ['low', 'medium', 'high']:
            return jsonify({'error': 'Некорректный приоритет'}), 400
        
        # Проверка существования сайта
        site = Site.query.get(site_id)
        if not site:
            return jsonify({'error': 'Сайт не найден'}), 404
        
        # Получение статуса "Новое"
        new_status = TicketStatus.query.filter_by(name='Новое').first()
        if not new_status:
            return jsonify({'error': 'Статус "Новое" не найден'}), 500
        
        # Создание обращения
        ticket = Ticket(
            user_id=current_user_id,
            site_id=site_id,
            status_id=new_status.id,
            subject=subject,
            description=description,
            priority=priority,
            created_at=datetime.utcnow()
        )
        
        db.session.add(ticket)
        db.session.commit()
        
        return jsonify({
            'message': 'Обращение успешно создано',
            'ticket': {
                'id': ticket.id,
                'subject': ticket.subject,
                'status': 'Новое',
                'created_at': ticket.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        print(f"ERROR in create_ticket: {str(e)}")  # ← Для отладки
        db.session.rollback()
        return jsonify({'error': f'Ошибка при создании обращения: {str(e)}'}), 500

@tickets_bp.route('/<int:ticket_id>', methods=['GET'])
@jwt_required()
def get_ticket(ticket_id):
    """Получение конкретного обращения"""
    try:
        # ИСПРАВЛЕНО: преобразуем строку в число
        current_user_id = int(get_jwt_identity())
        
        user = User.query.get(current_user_id)
        ticket = Ticket.query.get(ticket_id)
        
        if not ticket:
            return jsonify({'error': 'Обращение не найдено'}), 404
        
        # Проверка прав доступа
        if user.role != 'admin' and ticket.user_id != current_user_id:
            return jsonify({'error': 'Доступ запрещен'}), 403
        
        return jsonify({
            'id': ticket.id,
            'subject': ticket.subject,
            'description': ticket.description,
            'priority': ticket.priority,
            'created_at': ticket.created_at.isoformat(),
            'updated_at': ticket.updated_at.isoformat(),
            'resolved_at': ticket.resolved_at.isoformat() if ticket.resolved_at else None,
            'status': {
                'id': ticket.status.id,
                'name': ticket.status.name,
                'color': ticket.status.color_code
            },
            'site': {
                'id': ticket.site.id,
                'name': ticket.site.name,
                'url': ticket.site.url
            },
            'author': {
                'id': ticket.author.id,
                'name': ticket.author.name
            }
        }), 200
        
    except Exception as e:
        print(f"ERROR in get_ticket: {str(e)}")
        return jsonify({'error': f'Ошибка при получении обращения: {str(e)}'}), 500

@tickets_bp.route('/<int:ticket_id>/status', methods=['PUT'])
@jwt_required()
def update_ticket_status(ticket_id):
    """Обновление статуса обращения (только для админов)"""
    try:
        # ИСПРАВЛЕНО: преобразуем строку в число
        current_user_id = int(get_jwt_identity())
        
        user = User.query.get(current_user_id)
        
        if user.role != 'admin':
            return jsonify({'error': 'Только администраторы могут изменять статус'}), 403
        
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Обращение не найдено'}), 404
        
        data = request.get_json()
        status_name = data.get('status')
        
        if not status_name:
            return jsonify({'error': 'Статус обязателен'}), 400
        
        new_status = TicketStatus.query.filter_by(name=status_name).first()
        if not new_status:
            return jsonify({'error': 'Статус не найден'}), 404
        
        ticket.status_id = new_status.id
        ticket.updated_at = datetime.utcnow()
        
        # Если статус "Решено", фиксируем время решения
        if status_name == 'Решено' and not ticket.resolved_at:
            ticket.resolved_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Статус успешно обновлен',
            'status': {
                'id': new_status.id,
                'name': new_status.name
            }
        }), 200
        
    except Exception as e:
        print(f"ERROR in update_ticket_status: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Ошибка при обновлении статуса: {str(e)}'}), 500

@tickets_bp.route('/sites', methods=['GET'])
@jwt_required()
def get_sites():
    """Получение списка сайтов для формы"""
    try:
        sites = Site.query.order_by(Site.name).all()
        
        sites_data = []
        for site in sites:
            sites_data.append({
                'id': site.id,
                'name': site.name,
                'url': site.url,
                'category': site.category
            })
        
        return jsonify({'sites': sites_data}), 200
        
    except Exception as e:
        print(f"ERROR in get_sites: {str(e)}")
        return jsonify({'error': f'Ошибка при получении сайтов: {str(e)}'}), 500