-- Jiantizi adaption for Bootcamp Week 1:
-- Rename Japanese language columns to Chinese equivalents
ALTER TABLE words RENAME COLUMN kanji TO jiantizi;
ALTER TABLE words RENAME COLUMN romaji TO pinyin; 