# Jiantizi adaption for Bootcamp Week 1:
# Test Chinese character storage

import pytest

def test_chinese_character_storage(app):
    with app.app_context():
        cursor = app.db.cursor()
        
        # Clear any existing data
        cursor.execute('DELETE FROM words')
        app.db.commit()
        
        test_data = [
            ('中文', 'zhōng wén', 'Chinese'),  # Will be first in ORDER BY
            ('你好', 'nǐ hǎo', 'hello'),
            ('学习', 'xué xí', 'study')
        ]
        
        for jiantizi, pinyin, english in test_data:
            cursor.execute('''
                INSERT INTO words (jiantizi, pinyin, english)
                VALUES (?, ?, ?)
            ''', (jiantizi, pinyin, english))
        app.db.commit()
        
        cursor.execute('SELECT * FROM words ORDER BY jiantizi')
        results = cursor.fetchall()
        
        for i, result in enumerate(results):
            assert result['jiantizi'] == test_data[i][0]
            assert result['pinyin'] == test_data[i][1]

def test_pinyin_tone_marks(app):
    with app.app_context():
        cursor = app.db.cursor()
        
        # Clear any existing data
        cursor.execute('DELETE FROM words')
        app.db.commit()
        
        test_pinyin = [
            ('中文', 'zhōng wén', 'Chinese'),  # Will be first in ORDER BY
            ('你好', 'nǐ hǎo', 'hello'),
            ('学习', 'xué xí', 'study')
        ]
        
        for jiantizi, pinyin, english in test_pinyin:
            cursor.execute('''
                INSERT INTO words (jiantizi, pinyin, english)
                VALUES (?, ?, ?)
            ''', (jiantizi, pinyin, english))
        app.db.commit()
        
        cursor.execute('SELECT pinyin FROM words ORDER BY jiantizi')
        results = cursor.fetchall()
        
        for i, result in enumerate(results):
            assert result['pinyin'] == test_pinyin[i][1]