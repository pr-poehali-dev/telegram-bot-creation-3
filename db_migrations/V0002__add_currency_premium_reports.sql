-- Таблица для хранения брюликов пользователей
CREATE TABLE IF NOT EXISTS user_currency (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    balance BIGINT DEFAULT 0,
    last_farm TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для премиум подписок
CREATE TABLE IF NOT EXISTS user_premium (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username VARCHAR(255),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Таблица для репортов от пользователей
CREATE TABLE IF NOT EXISTS user_reports (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username VARCHAR(255),
    report_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    viewed BOOLEAN DEFAULT FALSE
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_user_currency_user_id ON user_currency(user_id);
CREATE INDEX IF NOT EXISTS idx_user_premium_user_id ON user_premium(user_id);
CREATE INDEX IF NOT EXISTS idx_user_premium_expires ON user_premium(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_reports_viewed ON user_reports(viewed);