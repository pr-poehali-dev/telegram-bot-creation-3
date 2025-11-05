import json
import os
from typing import Dict, Any
import urllib.request
import urllib.error
import psycopg2

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Verify Telegram bot token, save it to DB, and set webhook
    Args: event - dict with httpMethod, body (contains token and webhook_url)
          context - object with request_id, function_name
    Returns: HTTP response with bot information or error
    '''
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    body_str = event.get('body', '{}')
    if not body_str or body_str == '':
        body_str = '{}'
    
    body_data = json.loads(body_str)
    token = body_data.get('token', '').strip()
    
    if not token:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Token is required'}),
            'isBase64Encoded': False
        }
    
    telegram_api_url = f'https://api.telegram.org/bot{token}/getMe'
    
    try:
        req = urllib.request.Request(telegram_api_url)
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if not result.get('ok'):
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'Invalid token'}),
                    'isBase64Encoded': False
                }
            
            bot_info = result.get('result', {})
            bot_id = bot_info.get('id')
            bot_username = bot_info.get('username')
            bot_first_name = bot_info.get('first_name')
            
            dsn = os.environ.get('DATABASE_URL')
            conn = psycopg2.connect(dsn)
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO bot_tokens (bot_token, bot_id, bot_username, bot_first_name) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                        (token, bot_id, bot_username, bot_first_name)
                    )
                    cur.execute("UPDATE bot_tokens SET is_active = FALSE WHERE bot_token != %s", (token,))
                    cur.execute("UPDATE bot_tokens SET is_active = TRUE WHERE bot_token = %s", (token,))
                    conn.commit()
            finally:
                conn.close()
            
            webhook_url = body_data.get('webhook_url', '')
            if webhook_url:
                webhook_api_url = f'https://api.telegram.org/bot{token}/setWebhook'
                webhook_data = json.dumps({'url': webhook_url}).encode('utf-8')
                webhook_req = urllib.request.Request(webhook_api_url, data=webhook_data, headers={'Content-Type': 'application/json'})
                try:
                    with urllib.request.urlopen(webhook_req, timeout=10) as webhook_response:
                        webhook_result = json.loads(webhook_response.read().decode('utf-8'))
                except Exception:
                    pass
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'bot': {
                        'id': bot_id,
                        'first_name': bot_first_name,
                        'username': bot_username
                    }
                }),
                'isBase64Encoded': False
            }
            
    except urllib.error.HTTPError as e:
        error_msg = 'Неверный токен или бот не найден'
        if e.code == 401:
            error_msg = 'Неверный токен'
        elif e.code == 404:
            error_msg = 'Бот не найден'
            
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': error_msg}),
            'isBase64Encoded': False
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': f'Ошибка сервера: {str(e)}'}),
            'isBase64Encoded': False
        }