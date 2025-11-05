-- Создание таблиц для системы управления Telegram ботом

-- Таблица пользователей с рангами менеджеров бота
CREATE TABLE IF NOT EXISTS bot_managers (
    id SERIAL PRIMARY KEY,
    telegram_username VARCHAR(255) UNIQUE NOT NULL,
    telegram_id BIGINT UNIQUE,
    manager_rank VARCHAR(50) NOT NULL CHECK (manager_rank IN ('founder', 'deputy', 'agent')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица чатов
CREATE TABLE IF NOT EXISTS chats (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT UNIQUE NOT NULL,
    chat_link VARCHAR(500),
    chat_title VARCHAR(500),
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT,
    ban_days INTEGER,
    banned_at TIMESTAMP,
    owner_username VARCHAR(255),
    owner_telegram_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица администраторов чатов
CREATE TABLE IF NOT EXISTS chat_admins (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    telegram_username VARCHAR(255) NOT NULL,
    telegram_id BIGINT,
    admin_level INTEGER NOT NULL CHECK (admin_level BETWEEN 1 AND 5),
    assigned_by_username VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chat_id, telegram_username)
);

-- Таблица глобальных банов
CREATE TABLE IF NOT EXISTS server_bans (
    id SERIAL PRIMARY KEY,
    telegram_username VARCHAR(255) NOT NULL,
    telegram_id BIGINT,
    banned_by_username VARCHAR(255),
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(telegram_username)
);

-- Таблица мутов
CREATE TABLE IF NOT EXISTS chat_mutes (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    telegram_username VARCHAR(255) NOT NULL,
    telegram_id BIGINT,
    muted_by_username VARCHAR(255),
    mute_duration_minutes INTEGER NOT NULL,
    muted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unmute_at TIMESTAMP NOT NULL
);

-- Таблица постоянных банов в чате
CREATE TABLE IF NOT EXISTS chat_bans (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    telegram_username VARCHAR(255) NOT NULL,
    telegram_id BIGINT,
    banned_by_username VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chat_id, telegram_username)
);

-- Таблица токенов ботов
CREATE TABLE IF NOT EXISTS bot_tokens (
    id SERIAL PRIMARY KEY,
    bot_token TEXT NOT NULL,
    bot_id BIGINT NOT NULL,
    bot_username VARCHAR(255),
    bot_first_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Вставка основателя и зама основателя
INSERT INTO bot_managers (telegram_username, manager_rank) 
VALUES 
    ('Mad_SVO', 'founder'),
    ('Andrian_SVO', 'deputy')
ON CONFLICT (telegram_username) DO NOTHING;

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_chat_admins_chat_id ON chat_admins(chat_id);
CREATE INDEX IF NOT EXISTS idx_chat_admins_username ON chat_admins(telegram_username);
CREATE INDEX IF NOT EXISTS idx_server_bans_username ON server_bans(telegram_username);
CREATE INDEX IF NOT EXISTS idx_chat_mutes_chat_id ON chat_mutes(chat_id);
CREATE INDEX IF NOT EXISTS idx_chat_mutes_unmute_at ON chat_mutes(unmute_at);
CREATE INDEX IF NOT EXISTS idx_chat_bans_chat_id ON chat_bans(chat_id);