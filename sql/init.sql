CREATE TABLE achievement_messages (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    invoking_user_id INT NOT NULL,
    target_user_id INT NOT NULL,
    message_text TEXT NOT NULL,
    prompt_text TEXT,
    timestamp TIMESTAMPTZ NOT NULL
);

comment on column achievement_messages.chat_id is 'The chat ID';
comment on column achievement_messages.invoking_user_id is 'The user ID of a peron who invoked give achievement command';
comment on column achievement_messages.target_user_id is 'The user ID of a person who was targeted for an achievement';
comment on column achievement_messages.message_text is 'The message text';
comment on column achievement_messages.message_text is 'Detected prompt text (null if the prompt was unknown)';
comment on column achievement_messages.timestamp is 'The timestamp of the message';

CREATE TABLE chat_achievements (
    id SERIAL PRIMARY KEY,
    file_id TEXT,
    file_unique_id TEXT,
    type VARCHAR NOT NULL,
    engraving_text TEXT,
    times_achieved INT,
    index_in_sticker_set INT NOT NULL,
    chat_id BIGINT NOT NULL,
    sticker_set_name TEXT NOT NULL,
    sticker_set_owner_id INT NOT NULL,
    file_path TEXT NOT NULL
);

comment on column chat_achievements.file_id is 'Telegram sticker id (not a primary since two different stickers might have the same id in telegram)';
comment on column chat_achievements.file_unique_id is 'Telegram internal file id';
comment on column chat_achievements.type is 'achievement, description or empty';
comment on column chat_achievements.times_achieved is 'Number of times this achievement was taken (NULL if stickers type is not achievement)';
comment on column chat_achievements.index_in_sticker_set is 'The index of sticker in sticker pack';
comment on column chat_achievements.chat_id is 'The chat ID';
comment on column chat_achievements.sticker_set_name is 'The name of the sticker pack';
comment on column chat_achievements.sticker_set_owner_id is 'The user ID of owner of sticker pack';
comment on column chat_achievements.file_path is 'Path to the sticker file source';

CREATE TABLE user_achievements (
    id SERIAL PRIMARY KEY,
    file_id TEXT,
    file_unique_id TEXT,
    type VARCHAR NOT NULL,
    engraving_text TEXT,
    index_in_sticker_set INT NOT NULL,
    user_id BIGINT NOT NULL,
    chat_id BIGINT NOT NULL,
    sticker_set_name TEXT NOT NULL,
    file_path TEXT NOT NULL
);

comment on column user_achievements.file_id is 'Telegram sticker id (not a primary since two different stickers might have the same id in telegram)';
comment on column user_achievements.type is 'achievement, description, profile, profile_description or empty';
comment on column user_achievements.index_in_sticker_set is 'The index of sticker in sticker pack';
comment on column user_achievements.user_id is 'The user ID';
comment on column user_achievements.chat_id is 'The chat ID';
comment on column user_achievements.sticker_set_name is 'The name of the sticker pack';
comment on column user_achievements.file_path is 'Path to the sticker file source';
