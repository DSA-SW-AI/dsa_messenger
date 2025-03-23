CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    staffid TEXT UNIQUE NOT NULL,
    firstname TEXT NOT NULL,
    lastname TEXT NOT NULL,
    directorate TEXT NOT NULL,  -- Stores the selected directorate
    password TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,  -- Group name (directorate or general group)
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    group_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (group_id) REFERENCES groups(id),
    UNIQUE(user_id, group_id)  -- Prevent duplicate entries
);


CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    group_id INTEGER,
    private_chat_id INTEGER,
    message TEXT,
    message_type TEXT CHECK(message_type IN ('text', 'image', 'file', 'audio', 'video')) NOT NULL DEFAULT 'text',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    CHECK (group_id IS NOT NULL OR private_chat_id IS NOT NULL),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (group_id) REFERENCES groups(id),
    FOREIGN KEY (private_chat_id) REFERENCES private_chats(id)
);


CREATE TABLE IF NOT EXISTS private_chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user1_id INTEGER NOT NULL,  -- One user
    user2_id INTEGER NOT NULL,  -- The other user
    UNIQUE(user1_id, user2_id), -- ✅ Prevent duplicate chat creation
    FOREIGN KEY (user1_id) REFERENCES users(id),
    FOREIGN KEY (user2_id) REFERENCES users(id)
);
