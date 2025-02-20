-- Jiantizi adaption for Bootcamp Week 1:
-- Convert existing Japanese data to Chinese equivalents

-- Update study materials with Chinese equivalents
UPDATE words 
SET jiantizi = CASE english
    WHEN 'to study' THEN '学习'
    WHEN 'to speak' THEN '说'
    WHEN 'to go' THEN '去'
    WHEN 'to exercise' THEN '运动'
    -- Add more mappings
    ELSE jiantizi
END,
pinyin = CASE english
    WHEN 'to study' THEN 'xué xí'
    WHEN 'to speak' THEN 'shuō'
    WHEN 'to go' THEN 'qù'
    WHEN 'to exercise' THEN 'yùn dòng'
    -- Add more mappings
    ELSE pinyin
END
WHERE english IN ('to study', 'to speak', 'to go', 'to exercise'); 