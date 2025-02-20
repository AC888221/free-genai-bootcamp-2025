# Jiantizi adaption for Bootcamp Week 1:
# Test data initialization

test_words = [
    {
        'jiantizi': '学习',
        'pinyin': 'xué xí',
        'english': 'to study',
        'parts': [
            {'jiantizi': '学', 'pinyin': ['xué']},
            {'jiantizi': '习', 'pinyin': ['xí']}
        ]
    },
    {
        'jiantizi': '好',
        'pinyin': 'hǎo',
        'english': 'good',
        'parts': [
            {'jiantizi': '好', 'pinyin': ['hǎo']}
        ]
    }
]

def init_test_data(db):
    cursor = db.cursor()
    for word in test_words:
        cursor.execute('''
            INSERT INTO words (jiantizi, pinyin, english, parts)
            VALUES (?, ?, ?, ?)
        ''', (word['jiantizi'], word['pinyin'], word['english'], str(word['parts'])))
    db.commit() 