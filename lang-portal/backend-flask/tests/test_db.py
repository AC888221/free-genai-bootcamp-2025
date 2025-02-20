# Jiantizi adaption for Bootcamp Week 1:
# Test database operations with Chinese characters

import pytest

def test_db_chinese_storage(app):
    with app.app_context():
        cursor = app.db.cursor()
        cursor.execute('''
            INSERT INTO words (jiantizi, pinyin, english)
            VALUES (?, ?, ?)
        ''', ('你好', 'nǐ hǎo', 'hello'))
        app.db.commit()

        cursor.execute('SELECT * FROM words WHERE jiantizi = ?', ('你好',))
        result = cursor.fetchone()
        assert result['jiantizi'] == '你好'
        assert result['pinyin'] == 'nǐ hǎo'

def test_db_encoding(app):
    with app.app_context():
        cursor = app.db.cursor()
        cursor.execute('PRAGMA encoding')
        result = cursor.fetchone()
        assert result[0] == 'UTF-8' 