CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT,
    user_id INT,
    message_text TEXT,
    timestamp TIMESTAMPTZ
);
