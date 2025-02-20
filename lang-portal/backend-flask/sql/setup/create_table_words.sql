CREATE TABLE IF NOT EXISTS words (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  jiantizi TEXT NOT NULL,  -- Simplified Chinese characters
  pinyin TEXT NOT NULL,    -- Romanized pronunciation with tone marks
  english TEXT NOT NULL,
  parts TEXT NOT NULL      -- Store parts as JSON string
);