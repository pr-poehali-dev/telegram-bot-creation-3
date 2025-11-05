import json
import os
from typing import Dict, Any, Optional, List
import urllib.request
import urllib.error
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

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

def send_telegram_message(bot_token: str, chat_id: int, text: str):
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    data = json.dumps({'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception:
        pass

def kick_chat_member(bot_token: str, chat_id: int, user_id: int):
    url = f'https://api.telegram.org/bot{bot_token}/banChatMember'
    data = json.dumps({'chat_id': chat_id, 'user_id': user_id}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            unban_url = f'https://api.telegram.org/bot{bot_token}/unbanChatMember'
            unban_data = json.dumps({'chat_id': chat_id, 'user_id': user_id, 'only_if_banned': True}).encode('utf-8')
            unban_req = urllib.request.Request(unban_url, data=unban_data, headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(unban_req, timeout=10)
            return result
    except Exception:
        pass

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

def handle_command(message: Dict[str, Any], bot_token: str) -> Optional[str]:
    text = message.get('text', '')
    chat_id = message['chat']['id']
    from_user = message['from']
    from_username = from_user.get('username', '')
    
    if not text.startswith('/'):
        return None
    
    parts = text.split()
    command = parts[0].lower().replace('@', '').split('@')[0]
    args = parts[1:]
    
    manager_rank = get_manager_rank(from_username)
    admin_level = get_chat_admin_level(chat_id, from_username)
    is_owner = is_chat_owner(chat_id, from_username)
    
    if command == '/commands':
        return """<b>📋 Доступные команды:</b>

<b>👥 Для всех пользователей:</b>
/commands - Показать список команд
/profile [юзернейм] - Показать профиль пользователя

<b>👔 Команды менеджеров бота:</b>
<b>Основатель:</b>
/szamrang [юзернейм] - Назначить зама основателя
/deltechat [ссылка] - Удалить бота из чата
/banchat [ссылка] [причина] [дни] - Заблокировать чат

<b>Зам. Основателя:</b>
/agent [юзернейм] - Назначить сотрудника
/serverban [юзернейм] - Глобальный бан пользователя

<b>Сотрудник:</b>
/agents - Список сотрудников
/chats - Список чатов

<b>🛡️ Команды модерации чата:</b>
<b>Владелец:</b>
/unrang [юзернейм] - Снять ранг
/gban [юзернейм] - Забанить навсегда

<b>Администратор 5 уровня:</b>
/rang [юзернейм] [уровень 1-5] - Назначить админа

<b>Администратор 2 уровня:</b>
/mute [юзернейм] [минуты] - Замутить пользователя"""
    
    if command == '/profile':
        target_username = args[0].replace('@', '') if args else from_username
        
        manager_rank_target = get_manager_rank(target_username)
        admin_level_target = get_chat_admin_level(chat_id, target_username)
        
        rank_text = 'Пользователь'
        if manager_rank_target == 'founder':
            rank_text = 'Основатель бота'
        elif manager_rank_target == 'deputy':
            rank_text = 'Зам. Основателя'
        elif manager_rank_target == 'agent':
            rank_text = 'Сотрудник'
        elif admin_level_target:
            rank_text = f'Администратор {admin_level_target} уровня'
        elif is_chat_owner(chat_id, target_username):
            rank_text = 'Владелец чата'
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT telegram_id FROM bot_managers WHERE telegram_username = %s",
                    (target_username,)
                )
                result = cur.fetchone()
                user_id = result['telegram_id'] if result else 'Не указан'
        
        return f"""<b>👤 Профиль пользователя</b>

Юзернейм: @{target_username}
Ранг: {rank_text}
ID: {user_id}"""
    
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
                        "INSERT INTO server_bans (telegram_username, banned_by_username) VALUES (%s, %s) ON CONFLICT (telegram_username) DO NOTHING",
                        (target_username, from_username)
                    )
                    conn.commit()
            return f"✅ @{target_username} получил глобальный бан"
    
    if manager_rank in ['founder', 'deputy', 'agent']:
        if command == '/agents':
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT telegram_username, manager_rank FROM bot_managers WHERE manager_rank = 'agent'")
                    agents = cur.fetchall()
            if agents:
                agent_list = '\n'.join([f"• @{a['telegram_username']}" for a in agents])
                return f"<b>👥 Список сотрудников:</b>\n\n{agent_list}"
            return "Сотрудников пока нет"
        
        if command == '/chats':
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT chat_id, chat_title FROM chats LIMIT 20")
                    chats_list = cur.fetchall()
            if chats_list:
                chat_text = '\n'.join([f"• {c['chat_title'] or 'Чат'} (ID: {c['chat_id']})" for c in chats_list])
                return f"<b>💬 Список чатов:</b>\n\n{chat_text}"
            return "Чатов пока нет"
    
    if is_owner:
        if command == '/unrang' and len(args) >= 1:
            target_username = args[0].replace('@', '')
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM chat_admins WHERE chat_id = %s AND telegram_username = %s",
                        (chat_id, target_username)
                    )
                    conn.commit()
            return f"✅ @{target_username} снят с ранга"
        
        if command == '/gban' and len(args) >= 1:
            target_username = args[0].replace('@', '')
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT telegram_id FROM bot_managers WHERE telegram_username = %s",
                        (target_username,)
                    )
                    user_result = cur.fetchone()
                    if user_result and user_result['telegram_id']:
                        kick_chat_member(bot_token, chat_id, user_result['telegram_id'])
                    
                    cur.execute(
                        "INSERT INTO chat_bans (chat_id, telegram_username, banned_by_username) VALUES (%s, %s, %s) ON CONFLICT (chat_id, telegram_username) DO NOTHING",
                        (chat_id, target_username, from_username)
                    )
                    conn.commit()
            return f"✅ @{target_username} забанен навсегда"
    
    if (is_owner or (admin_level and admin_level >= 5)):
        if command == '/rang' and len(args) >= 2:
            target_username = args[0].replace('@', '')
            try:
                level = int(args[1])
                if 1 <= level <= 5:
                    with get_db_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                "INSERT INTO chat_admins (chat_id, telegram_username, admin_level, assigned_by_username) VALUES (%s, %s, %s, %s) ON CONFLICT (chat_id, telegram_username) DO UPDATE SET admin_level = %s",
                                (chat_id, target_username, level, from_username, level)
                            )
                            conn.commit()
                    return f"✅ @{target_username} назначен Администратором {level} уровня"
            except ValueError:
                return "❌ Уровень должен быть числом от 1 до 5"
    
    if (is_owner or (admin_level and admin_level >= 2)):
        if command == '/mute' and len(args) >= 2:
            target_username = args[0].replace('@', '')
            try:
                minutes = int(args[1])
                unmute_at = datetime.now() + timedelta(minutes=minutes)
                unmute_timestamp = int(unmute_at.timestamp())
                
                with get_db_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        cur.execute(
                            "SELECT telegram_id FROM bot_managers WHERE telegram_username = %s",
                            (target_username,)
                        )
                        user_result = cur.fetchone()
                        if user_result and user_result['telegram_id']:
                            restrict_chat_member(bot_token, chat_id, user_result['telegram_id'], unmute_timestamp)
                        
                        cur.execute(
                            "INSERT INTO chat_mutes (chat_id, telegram_username, muted_by_username, mute_duration_minutes, unmute_at) VALUES (%s, %s, %s, %s, %s)",
                            (chat_id, target_username, from_username, minutes, unmute_at)
                        )
                        conn.commit()
                return f"✅ @{target_username} замучен на {minutes} минут"
            except ValueError:
                return "❌ Время должно быть числом (в минутах)"
    
    return None

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Telegram bot webhook handler for commands and moderation
    Args: event - dict with httpMethod, body (Telegram update)
          context - object with request_id, function_name
    Returns: HTTP response
    '''
    method: str = event.get('httpMethod', 'POST')
    
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
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    body_str = event.get('body', '{}')
    update = json.loads(body_str)
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT bot_token FROM bot_tokens WHERE is_active = TRUE LIMIT 1")
            token_result = cur.fetchone()
    
    if not token_result:
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'ok': True}),
            'isBase64Encoded': False
        }
    
    bot_token = token_result['bot_token']
    
    if 'message' in update:
        message = update['message']
        chat_id = message['chat']['id']
        from_user = message['from']
        from_username = from_user.get('username', '')
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO chats (chat_id, chat_title, owner_username) VALUES (%s, %s, %s) ON CONFLICT (chat_id) DO NOTHING",
                    (chat_id, message['chat'].get('title', ''), from_username)
                )
                conn.commit()
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT telegram_username FROM server_bans WHERE telegram_username = %s", (from_username,))
                is_banned = cur.fetchone()
        
        if is_banned:
            kick_chat_member(bot_token, chat_id, from_user['id'])
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'ok': True}),
                'isBase64Encoded': False
            }
        
        response_text = handle_command(message, bot_token)
        
        if response_text:
            send_telegram_message(bot_token, chat_id, response_text)
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'ok': True}),
        'isBase64Encoded': False
    }
