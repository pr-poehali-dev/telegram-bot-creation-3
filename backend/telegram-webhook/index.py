import json
import os
from typing import Dict, Any, Optional, List
import urllib.request
import urllib.error
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import random

def get_db_connection():
    dsn = os.environ.get('DATABASE_URL')
    return psycopg2.connect(dsn)

def get_manager_rank(username: str) -> Optional[str]:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT manager_rank FROM bot_managers WHERE telegram_username = %s",
                (username,)
            )
            result = cur.fetchone()
            return result['manager_rank'] if result else None

def get_chat_admin_level(chat_id: int, username: str) -> Optional[int]:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT admin_level FROM chat_admins WHERE chat_id = %s AND telegram_username = %s",
                (chat_id, username)
            )
            result = cur.fetchone()
            return result['admin_level'] if result else None

def is_chat_owner(chat_id: int, username: str) -> bool:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT owner_username FROM chats WHERE chat_id = %s",
                (chat_id,)
            )
            result = cur.fetchone()
            return result and result['owner_username'] == username

def get_user_balance(user_id: int, username: str) -> int:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT balance FROM user_currency WHERE user_id = %s",
                (user_id,)
            )
            result = cur.fetchone()
            if not result:
                cur.execute(
                    "INSERT INTO user_currency (user_id, username, balance) VALUES (%s, %s, 0) RETURNING balance",
                    (user_id, username)
                )
                conn.commit()
                return 0
            return result['balance']

def update_user_balance(user_id: int, username: str, amount: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO user_currency (user_id, username, balance, updated_at) 
                   VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                   ON CONFLICT (user_id) 
                   DO UPDATE SET balance = user_currency.balance + %s, username = %s, updated_at = CURRENT_TIMESTAMP""",
                (user_id, username, amount, amount, username)
            )
            conn.commit()

def get_user_premium(user_id: int) -> Optional[datetime]:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT expires_at FROM user_premium WHERE user_id = %s AND expires_at > CURRENT_TIMESTAMP",
                (user_id,)
            )
            result = cur.fetchone()
            return result['expires_at'] if result else None

def add_user_premium(user_id: int, username: str, days: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO user_premium (user_id, username, expires_at)
                   VALUES (%s, %s, CURRENT_TIMESTAMP + INTERVAL '%s days')
                   ON CONFLICT (user_id)
                   DO UPDATE SET expires_at = GREATEST(user_premium.expires_at, CURRENT_TIMESTAMP) + INTERVAL '%s days', username = %s""",
                (user_id, username, days, days, username)
            )
            conn.commit()

def send_telegram_message(bot_token: str, chat_id: int, text: str, reply_markup: Optional[Dict] = None):
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
    if reply_markup:
        payload['reply_markup'] = reply_markup
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception:
        pass

def delete_telegram_message(bot_token: str, chat_id: int, message_id: int):
    url = f'https://api.telegram.org/bot{bot_token}/deleteMessage'
    data = json.dumps({'chat_id': chat_id, 'message_id': message_id}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception:
        pass

def ban_chat_member(bot_token: str, chat_id: int, user_id: int, until_date: Optional[int] = None):
    url = f'https://api.telegram.org/bot{bot_token}/banChatMember'
    payload = {'chat_id': chat_id, 'user_id': user_id}
    if until_date:
        payload['until_date'] = until_date
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception:
        pass

def unban_chat_member(bot_token: str, chat_id: int, user_id: int):
    url = f'https://api.telegram.org/bot{bot_token}/unbanChatMember'
    data = json.dumps({'chat_id': chat_id, 'user_id': user_id, 'only_if_banned': True}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception:
        pass

def kick_chat_member(bot_token: str, chat_id: int, user_id: int):
    ban_chat_member(bot_token, chat_id, user_id)
    unban_chat_member(bot_token, chat_id, user_id)

def restrict_chat_member(bot_token: str, chat_id: int, user_id: int, until_timestamp: int):
    url = f'https://api.telegram.org/bot{bot_token}/restrictChatMember'
    permissions = {
        'can_send_messages': False,
        'can_send_media_messages': False,
        'can_send_polls': False,
        'can_send_other_messages': False,
        'can_add_web_page_previews': False,
        'can_change_info': False,
        'can_invite_users': False,
        'can_pin_messages': False
    }
    data = json.dumps({
        'chat_id': chat_id,
        'user_id': user_id,
        'permissions': permissions,
        'until_date': until_timestamp
    }).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception:
        pass

def unrestrict_chat_member(bot_token: str, chat_id: int, user_id: int):
    url = f'https://api.telegram.org/bot{bot_token}/restrictChatMember'
    permissions = {
        'can_send_messages': True,
        'can_send_media_messages': True,
        'can_send_polls': True,
        'can_send_other_messages': True,
        'can_add_web_page_previews': True,
        'can_change_info': False,
        'can_invite_users': False,
        'can_pin_messages': False
    }
    data = json.dumps({
        'chat_id': chat_id,
        'user_id': user_id,
        'permissions': permissions
    }).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception:
        pass

def set_chat_title(bot_token: str, chat_id: int, title: str):
    url = f'https://api.telegram.org/bot{bot_token}/setChatTitle'
    data = json.dumps({'chat_id': chat_id, 'title': title}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception:
        pass

def get_user_id_by_username(username: str) -> Optional[int]:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT telegram_id FROM bot_managers WHERE telegram_username = %s",
                (username,)
            )
            result = cur.fetchone()
            if result and result['telegram_id']:
                return result['telegram_id']
            
            cur.execute(
                "SELECT user_id FROM user_currency WHERE username = %s",
                (username,)
            )
            result = cur.fetchone()
            return result['user_id'] if result else None

def handle_command(message: Dict[str, Any], bot_token: str) -> Optional[str]:
    text = message.get('text', '')
    chat_id = message['chat']['id']
    from_user = message['from']
    from_username = from_user.get('username', '')
    from_user_id = from_user['id']
    message_id = message['message_id']
    is_private = message['chat']['type'] == 'private'
    
    if not text.startswith('/'):
        return None
    
    parts = text.split(maxsplit=1)
    command = parts[0].lower().replace('@', '').split('@')[0]
    args_text = parts[1] if len(parts) > 1 else ''
    args = args_text.split()
    
    manager_rank = get_manager_rank(from_username)
    admin_level = get_chat_admin_level(chat_id, from_username)
    is_owner = is_chat_owner(chat_id, from_username)
    
    # Команда /me - для всех пользователей
    if command == '/me':
        rank_text = 'Пользователь'
        if manager_rank == 'founder':
            rank_text = '👑 Основатель бота'
        elif manager_rank == 'deputy':
            rank_text = '⭐ Зам. Основателя'
        elif manager_rank == 'agent':
            rank_text = '🎖️ Сотрудник'
        elif is_owner:
            rank_text = '👔 Владелец чата'
        elif admin_level:
            rank_text = f'🛡️ Администратор {admin_level} уровня'
        
        balance = get_user_balance(from_user_id, from_username)
        premium = get_user_premium(from_user_id)
        premium_text = f"до {premium.strftime('%d.%m.%Y %H:%M')}" if premium else "Нет"
        
        return f"""<b>👤 Ваш профиль</b>

Юзернейм: @{from_username}
Ранг: {rank_text}
ID: {from_user_id}
💎 Брюликов: {balance}
⭐ Premium: {premium_text}"""
    
    # Команда /balance - показать баланс
    if command == '/balance':
        balance = get_user_balance(from_user_id, from_username)
        return f"💎 Ваш баланс: <b>{balance}</b> брюликов"
    
    # Команда /farm - получить брюлики
    if command == '/farm':
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT last_farm FROM user_currency WHERE user_id = %s",
                    (from_user_id,)
                )
                result = cur.fetchone()
                
                if result and result['last_farm']:
                    next_farm = result['last_farm'] + timedelta(hours=1)
                    if datetime.now() < next_farm:
                        wait_minutes = int((next_farm - datetime.now()).total_seconds() / 60)
                        return f"⏰ Вы уже собирали брюлики! Следующий фарм через {wait_minutes} минут"
                
                amount = random.randint(10, 100)
                cur.execute(
                    """INSERT INTO user_currency (user_id, username, balance, last_farm, updated_at)
                       VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                       ON CONFLICT (user_id)
                       DO UPDATE SET balance = user_currency.balance + %s, last_farm = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP""",
                    (from_user_id, from_username, amount, amount)
                )
                conn.commit()
                
                balance = get_user_balance(from_user_id, from_username)
                return f"✅ Вы собрали <b>{amount}</b> брюликов!\n💎 Текущий баланс: <b>{balance}</b>"
    
    # Команда /premium - купить или посмотреть подписку
    if command == '/premium':
        premium = get_user_premium(from_user_id)
        if premium:
            return f"⭐ У вас есть Premium подписка до {premium.strftime('%d.%m.%Y %H:%M')}"
        
        keyboard = {
            'inline_keyboard': [
                [{'text': '3 дня (100 💎)', 'callback_data': 'premium_3'}],
                [{'text': '7 дней (250 💎)', 'callback_data': 'premium_7'}],
                [{'text': '30 дней (1000 💎)', 'callback_data': 'premium_30'}]
            ]
        }
        
        send_telegram_message(
            bot_token,
            chat_id,
            """<b>⭐ Premium подписка</b>

С Premium вы можете:
• Писать сообщения от лица бота (/pmessage)

Выберите подписку:""",
            reply_markup=keyboard
        )
        return None
    
    # Команда /pmessage - для премиум пользователей
    if command == '/pmessage':
        premium = get_user_premium(from_user_id)
        if not premium:
            return "❌ Эта команда доступна только для Premium пользователей. Используйте /premium для покупки"
        
        if not args_text:
            return "❌ Использование: /pmessage текст сообщения"
        
        delete_telegram_message(bot_token, chat_id, message_id)
        send_telegram_message(bot_token, chat_id, args_text)
        return None
    
    # Команда /sreport - отправить репорт (только в ЛС)
    if command == '/sreport':
        if not is_private:
            return "❌ Эта команда доступна только в личных сообщениях с ботом"
        
        if not args_text:
            return "❌ Использование: /sreport текст репорта"
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO user_reports (user_id, username, report_text) VALUES (%s, %s, %s)",
                    (from_user_id, from_username, args_text)
                )
                conn.commit()
        
        return "✅ Ваш репорт отправлен сотрудникам!"
    
    # Команда /reports - для сотрудников+
    if command == '/reports':
        if manager_rank not in ['founder', 'deputy', 'agent']:
            return "❌ Эта команда доступна только для Сотрудников и выше"
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, user_id, username, report_text, created_at FROM user_reports WHERE viewed = FALSE ORDER BY created_at DESC LIMIT 10"
                )
                reports = cur.fetchall()
        
        if not reports:
            return "📋 Новых репортов нет"
        
        text = "<b>📋 Непрочитанные репорты:</b>\n\n"
        for r in reports:
            text += f"ID: {r['id']}\nОт: @{r['username']} (ID: {r['user_id']})\nТекст: {r['report_text']}\nДата: {r['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        
        return text
    
    # Команда /commands
    if command == '/commands':
        return """<b>📋 Доступные команды:</b>

<b>👥 Для всех пользователей:</b>
/me - Показать свой профиль и ранг
/balance - Показать баланс брюликов
/farm - Собрать брюлики (раз в час)
/premium - Купить Premium подписку
/commands - Показать список команд
/profile [юзернейм] - Показать профиль пользователя
/sreport текст - Отправить репорт (только в ЛС)

<b>⭐ Premium команды:</b>
/pmessage текст - Написать от лица бота

<b>👔 Команды менеджеров бота:</b>
<b>Основатель:</b>
/szamrang [юзернейм] - Назначить зама основателя
/deltechat [ссылка] - Удалить бота из чата
/banchat [ссылка] [причина] [дни] - Заблокировать чат

<b>Зам. Основателя:</b>
/agent [юзернейм] - Назначить сотрудника
/unagent [юзернейм] - Снять сотрудника
/serverban [юзернейм] - Глобальный бан
/brulik [юзернейм] [число] - Выдать брюлики

<b>Сотрудник:</b>
/agents - Список сотрудников
/chats - Список чатов
/reports - Просмотр репортов

<b>🛡️ Команды модерации чата:</b>
<b>Владелец:</b>
/unrang [юзернейм] - Снять ранг
/gban [юзернейм] - Забанить навсегда

<b>Администратор 5 уровня:</b>
/rang [юзернейм] [уровень 1-5] - Назначить админа
/chatname текст - Переименовать чат

<b>Администратор 4 уровня:</b>
/unban [юзернейм] - Разбанить пользователя
/tban [юзернейм] [причина] [время_минут] - Временный бан

<b>Администратор 2 уровня:</b>
/mute [юзернейм] [минуты] - Замутить пользователя
/unmute [юзернейм] - Размутить пользователя

<b>Администратор 1 уровня:</b>
/mutelist - Список замученных
/banlist - Список забаненных"""
    
    if command == '/profile':
        target_username = args[0].replace('@', '') if args else from_username
        
        manager_rank_target = get_manager_rank(target_username)
        admin_level_target = get_chat_admin_level(chat_id, target_username)
        
        rank_text = 'Пользователь'
        if manager_rank_target == 'founder':
            rank_text = '👑 Основатель бота'
        elif manager_rank_target == 'deputy':
            rank_text = '⭐ Зам. Основателя'
        elif manager_rank_target == 'agent':
            rank_text = '🎖️ Сотрудник'
        elif admin_level_target:
            rank_text = f'🛡️ Администратор {admin_level_target} уровня'
        elif is_chat_owner(chat_id, target_username):
            rank_text = '👔 Владелец чата'
        
        target_user_id = get_user_id_by_username(target_username)
        if target_user_id:
            balance = get_user_balance(target_user_id, target_username)
            premium = get_user_premium(target_user_id)
            premium_text = f"до {premium.strftime('%d.%m.%Y')}" if premium else "Нет"
        else:
            balance = 0
            premium_text = "Нет"
        
        return f"""<b>👤 Профиль пользователя</b>

Юзернейм: @{target_username}
Ранг: {rank_text}
ID: {target_user_id or 'Не указан'}
💎 Брюликов: {balance}
⭐ Premium: {premium_text}"""
    
    # Команды для Зам. Основателя+
    if manager_rank in ['founder', 'deputy']:
        if command == '/unagent' and len(args) >= 1:
            target_username = args[0].replace('@', '')
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM bot_managers WHERE telegram_username = %s AND manager_rank = 'agent'",
                        (target_username,)
                    )
                    if cur.rowcount > 0:
                        conn.commit()
                        return f"✅ @{target_username} снят с должности Сотрудника"
                    else:
                        return f"❌ @{target_username} не является Сотрудником"
        
        if command == '/brulik' and len(args) >= 2:
            target_username = args[0].replace('@', '')
            try:
                amount = int(args[1])
                target_user_id = get_user_id_by_username(target_username)
                if not target_user_id:
                    return f"❌ Пользователь @{target_username} не найден"
                
                update_user_balance(target_user_id, target_username, amount)
                new_balance = get_user_balance(target_user_id, target_username)
                return f"✅ Пользователю @{target_username} выдано {amount} брюликов. Новый баланс: {new_balance}"
            except ValueError:
                return "❌ Неверное количество брюликов"
    
    # Команды модерации - /gban для владельца
    if is_owner:
        if command == '/gban' and len(args) >= 1:
            target_username = args[0].replace('@', '')
            target_user_id = get_user_id_by_username(target_username)
            
            if not target_user_id:
                return f"❌ Пользователь @{target_username} не найден"
            
            ban_chat_member(bot_token, chat_id, target_user_id)
            
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO chat_bans (chat_id, user_id, username, banned_until) VALUES (%s, %s, %s, NULL) ON CONFLICT DO NOTHING",
                        (chat_id, target_user_id, target_username)
                    )
                    conn.commit()
            
            return f"✅ Пользователь @{target_username} забанен навсегда"
    
    # Команды для Администратора 5 уровня
    if admin_level and admin_level >= 5:
        if command == '/chatname' and args_text:
            result = set_chat_title(bot_token, chat_id, args_text)
            if result and result.get('ok'):
                return f"✅ Название чата изменено на: {args_text}"
            else:
                return "❌ Не удалось изменить название чата. Убедитесь, что бот является администратором"
    
    # Команды для Администратора 4 уровня
    if admin_level and admin_level >= 4:
        if command == '/unban' and len(args) >= 1:
            target_username = args[0].replace('@', '')
            target_user_id = get_user_id_by_username(target_username)
            
            if not target_user_id:
                return f"❌ Пользователь @{target_username} не найден"
            
            unban_chat_member(bot_token, chat_id, target_user_id)
            
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM chat_bans WHERE chat_id = %s AND user_id = %s",
                        (chat_id, target_user_id)
                    )
                    conn.commit()
            
            return f"✅ Пользователь @{target_username} разбанен"
        
        if command == '/tban' and len(args) >= 3:
            target_username = args[0].replace('@', '')
            reason = args[1]
            try:
                minutes = int(args[2])
                target_user_id = get_user_id_by_username(target_username)
                
                if not target_user_id:
                    return f"❌ Пользователь @{target_username} не найден"
                
                until_timestamp = int((datetime.now() + timedelta(minutes=minutes)).timestamp())
                ban_chat_member(bot_token, chat_id, target_user_id, until_timestamp)
                
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO chat_bans (chat_id, user_id, username, banned_until) VALUES (%s, %s, %s, %s) ON CONFLICT (chat_id, user_id) DO UPDATE SET banned_until = %s",
                            (chat_id, target_user_id, target_username, datetime.fromtimestamp(until_timestamp), datetime.fromtimestamp(until_timestamp))
                        )
                        conn.commit()
                
                return f"✅ Пользователь @{target_username} забанен на {minutes} минут. Причина: {reason}"
            except ValueError:
                return "❌ Неверное время бана"
    
    # Команды для Администратора 2 уровня
    if admin_level and admin_level >= 2:
        if command == '/mute' and len(args) >= 2:
            target_username = args[0].replace('@', '')
            try:
                minutes = int(args[1])
                target_user_id = get_user_id_by_username(target_username)
                
                if not target_user_id:
                    return f"❌ Пользователь @{target_username} не найден"
                
                until_timestamp = int((datetime.now() + timedelta(minutes=minutes)).timestamp())
                restrict_chat_member(bot_token, chat_id, target_user_id, until_timestamp)
                
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO chat_mutes (chat_id, user_id, username, muted_until) VALUES (%s, %s, %s, %s) ON CONFLICT (chat_id, user_id) DO UPDATE SET muted_until = %s",
                            (chat_id, target_user_id, target_username, datetime.fromtimestamp(until_timestamp), datetime.fromtimestamp(until_timestamp))
                        )
                        conn.commit()
                
                return f"✅ Пользователь @{target_username} замучен на {minutes} минут"
            except ValueError:
                return "❌ Неверное время мута"
        
        if command == '/unmute' and len(args) >= 1:
            target_username = args[0].replace('@', '')
            target_user_id = get_user_id_by_username(target_username)
            
            if not target_user_id:
                return f"❌ Пользователь @{target_username} не найден"
            
            unrestrict_chat_member(bot_token, chat_id, target_user_id)
            
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM chat_mutes WHERE chat_id = %s AND user_id = %s",
                        (chat_id, target_user_id)
                    )
                    conn.commit()
            
            return f"✅ Пользователь @{target_username} размучен"
    
    # Команды для Администратора 1 уровня
    if admin_level and admin_level >= 1:
        if command == '/mutelist':
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT username, muted_until FROM chat_mutes WHERE chat_id = %s AND muted_until > CURRENT_TIMESTAMP ORDER BY muted_until",
                        (chat_id,)
                    )
                    mutes = cur.fetchall()
            
            if not mutes:
                return "📋 Список замученных пуст"
            
            text = "<b>📋 Замученные пользователи:</b>\n\n"
            for m in mutes:
                text += f"@{m['username']} - до {m['muted_until'].strftime('%d.%m.%Y %H:%M')}\n"
            
            return text
        
        if command == '/banlist':
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT username, banned_until FROM chat_bans WHERE chat_id = %s ORDER BY banned_until NULLS LAST",
                        (chat_id,)
                    )
                    bans = cur.fetchall()
            
            if not bans:
                return "📋 Список забаненных пуст"
            
            text = "<b>📋 Забаненные пользователи:</b>\n\n"
            for b in bans:
                if b['banned_until']:
                    text += f"@{b['username']} - до {b['banned_until'].strftime('%d.%m.%Y %H:%M')}\n"
                else:
                    text += f"@{b['username']} - навсегда\n"
            
            return text
    
    # Остальные команды из оригинального кода
    if manager_rank == 'founder':
        if command == '/szamrang' and len(args) >= 1:
            target_username = args[0].replace('@', '')
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO bot_managers (telegram_username, manager_rank) VALUES (%s, %s) ON CONFLICT (telegram_username) DO UPDATE SET manager_rank = %s",
                        (target_username, 'deputy', 'deputy')
                    )
                    conn.commit()
            return f"✅ @{target_username} назначен Заместителем Основателя"
        
        if command == '/deltechat' and len(args) >= 1:
            return "⚠️ Для удаления бота из чата используйте настройки группы в Telegram"
        
        if command == '/banchat' and len(args) >= 3:
            chat_link = args[0]
            ban_days = int(args[-1])
            reason = ' '.join(args[1:-1])
            return f"✅ Чат {chat_link} заблокирован на {ban_days} дней. Причина: {reason}"
    
    if manager_rank in ['founder', 'deputy']:
        if command == '/agent' and len(args) >= 1:
            target_username = args[0].replace('@', '')
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO bot_managers (telegram_username, manager_rank) VALUES (%s, %s) ON CONFLICT (telegram_username) DO UPDATE SET manager_rank = %s",
                        (target_username, 'agent', 'agent')
                    )
                    conn.commit()
            return f"✅ @{target_username} назначен Сотрудником"
        
        if command == '/serverban' and len(args) >= 1:
            target_username = args[0].replace('@', '')
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO server_bans (username) VALUES (%s) ON CONFLICT DO NOTHING",
                        (target_username,)
                    )
                    conn.commit()
            return f"✅ @{target_username} получил глобальный бан"
    
    if manager_rank in ['founder', 'deputy', 'agent']:
        if command == '/agents':
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT telegram_username, manager_rank FROM bot_managers WHERE manager_rank IN ('founder', 'deputy', 'agent') ORDER BY CASE manager_rank WHEN 'founder' THEN 1 WHEN 'deputy' THEN 2 WHEN 'agent' THEN 3 END")
                    managers = cur.fetchall()
            
            text = "<b>👥 Сотрудники бота:</b>\n\n"
            for m in managers:
                rank_emoji = {'founder': '👑', 'deputy': '⭐', 'agent': '🎖️'}
                rank_name = {'founder': 'Основатель', 'deputy': 'Зам. Основателя', 'agent': 'Сотрудник'}
                text += f"{rank_emoji.get(m['manager_rank'], '•')} @{m['telegram_username']} - {rank_name.get(m['manager_rank'], '')}\n"
            
            return text
        
        if command == '/chats':
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT chat_id, chat_title, owner_username FROM chats ORDER BY chat_id")
                    chats = cur.fetchall()
            
            text = "<b>💬 Список чатов:</b>\n\n"
            for c in chats:
                text += f"Чат ID: {c['chat_id']}\nНазвание: {c['chat_title']}\nВладелец: @{c['owner_username']}\n\n"
            
            return text
    
    if is_owner or (admin_level and admin_level >= 5):
        if command == '/rang' and len(args) >= 2:
            target_username = args[0].replace('@', '')
            try:
                level = int(args[1])
                if level < 1 or level > 5:
                    return "❌ Уровень администратора должен быть от 1 до 5"
                
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO chat_admins (chat_id, telegram_username, admin_level) VALUES (%s, %s, %s) ON CONFLICT (chat_id, telegram_username) DO UPDATE SET admin_level = %s",
                            (chat_id, target_username, level, level)
                        )
                        conn.commit()
                
                return f"✅ @{target_username} назначен Администратором {level} уровня"
            except ValueError:
                return "❌ Неверный уровень администратора"
    
    if is_owner:
        if command == '/unrang' and len(args) >= 1:
            target_username = args[0].replace('@', '')
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM chat_admins WHERE chat_id = %s AND telegram_username = %s",
                        (chat_id, target_username)
                    )
                    if cur.rowcount > 0:
                        conn.commit()
                        return f"✅ Ранг @{target_username} снят"
                    else:
                        return f"❌ @{target_username} не является администратором"
    
    return None

def handle_callback_query(callback_query: Dict[str, Any], bot_token: str):
    data = callback_query.get('data', '')
    user = callback_query['from']
    user_id = user['id']
    username = user.get('username', '')
    chat_id = callback_query['message']['chat']['id']
    message_id = callback_query['message']['message_id']
    
    if data.startswith('premium_'):
        days_map = {'premium_3': 3, 'premium_7': 7, 'premium_30': 30}
        cost_map = {'premium_3': 100, 'premium_7': 250, 'premium_30': 1000}
        
        days = days_map.get(data, 0)
        cost = cost_map.get(data, 0)
        
        if days == 0:
            return
        
        balance = get_user_balance(user_id, username)
        
        if balance < cost:
            url = f'https://api.telegram.org/bot{bot_token}/answerCallbackQuery'
            answer_data = json.dumps({
                'callback_query_id': callback_query['id'],
                'text': f'❌ Недостаточно брюликов! У вас: {balance}, нужно: {cost}',
                'show_alert': True
            }).encode('utf-8')
            req = urllib.request.Request(url, data=answer_data, headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(req, timeout=10)
            return
        
        update_user_balance(user_id, username, -cost)
        add_user_premium(user_id, username, days)
        
        url = f'https://api.telegram.org/bot{bot_token}/editMessageText'
        edit_data = json.dumps({
            'chat_id': chat_id,
            'message_id': message_id,
            'text': f'✅ Вы успешно приобрели Premium подписку на {days} дней!\n\nТеперь вы можете использовать /pmessage для написания от лица бота',
            'parse_mode': 'HTML'
        }).encode('utf-8')
        req = urllib.request.Request(url, data=edit_data, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=10)
        
        url = f'https://api.telegram.org/bot{bot_token}/answerCallbackQuery'
        answer_data = json.dumps({
            'callback_query_id': callback_query['id'],
            'text': f'✅ Premium активирован на {days} дней!',
            'show_alert': False
        }).encode('utf-8')
        req = urllib.request.Request(url, data=answer_data, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=10)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Handle Telegram webhook updates for bot commands and moderation
    Args: event - webhook update from Telegram, context - function execution context
    Returns: HTTP response with status 200
    '''
    method = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    body = json.loads(event.get('body', '{}'))
    
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Bot token not configured'}),
            'isBase64Encoded': False
        }
    
    if 'callback_query' in body:
        handle_callback_query(body['callback_query'], bot_token)
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'ok': True}),
            'isBase64Encoded': False
        }
    
    if 'message' not in body:
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'ok': True}),
            'isBase64Encoded': False
        }
    
    message = body['message']
    
    if 'new_chat_members' in message:
        chat_id = message['chat']['id']
        chat_title = message['chat'].get('title', 'Unknown')
        owner_username = message['from'].get('username', 'Unknown')
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO chats (chat_id, chat_title, owner_username) VALUES (%s, %s, %s) ON CONFLICT (chat_id) DO UPDATE SET chat_title = %s, owner_username = %s",
                    (chat_id, chat_title, owner_username, chat_title, owner_username)
                )
                conn.commit()
        
        welcome_text = """👋 Привет! Я бот для управления чатом.

Используйте /commands для просмотра всех доступных команд."""
        send_telegram_message(bot_token, chat_id, welcome_text)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'ok': True}),
            'isBase64Encoded': False
        }
    
    response_text = handle_command(message, bot_token)
    
    if response_text:
        chat_id = message['chat']['id']
        send_telegram_message(bot_token, chat_id, response_text)
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'ok': True}),
        'isBase64Encoded': False
    }
