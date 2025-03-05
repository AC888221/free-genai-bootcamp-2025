# word_collection.py (added back)

import config
import sqlite3
import requests
import streamlit as st
from flask import Flask, request, jsonify
from flask_cors import cross_origin

def fetch_words_from_db(db_path, page=1, words_per_page=50, sort_by='jiantizi', order='asc'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    offset = (page - 1) * words_per_page

    valid_columns = ['jiantizi', 'pinyin', 'english', 'correct_count', 'wrong_count']
    if sort_by not in valid_columns:
        sort_by = 'jiantizi'
    if order not in ['asc', 'desc']:
        order = 'asc'

    cursor.execute(f'''
        SELECT w.id, w.jiantizi, w.pinyin, w.english, 
            COALESCE(r.correct_count, 0) AS correct_count,
            COALESCE(r.wrong_count, 0) AS wrong_count
        FROM words w
        LEFT JOIN word_reviews r ON w.id = r.word_id
        ORDER BY {sort_by} {order}
        LIMIT ? OFFSET ?
    ''', (words_per_page, offset))
    words = cursor.fetchall()

    cursor.execute('SELECT COUNT(*) FROM words')
    total_words = cursor.fetchone()[0]
    total_pages = (total_words + words_per_page - 1) // words_per_page

    conn.close()
    return words, total_pages, total_words

def fetch_word_from_db(db_path, word_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT w.id, w.jiantizi, w.pinyin, w.english,
               COALESCE(r.correct_count, 0) AS correct_count,
               COALESCE(r.wrong_count, 0) AS wrong_count,
               GROUP_CONCAT(DISTINCT g.id || '::' || g.name) as groups
        FROM words w
        LEFT JOIN word_reviews r ON w.id = r.word_id
        LEFT JOIN word_groups wg ON w.id = wg.word_id
        LEFT JOIN groups g ON wg.group_id = g.id
        WHERE w.id = ?
        GROUP BY w.id
    ''', (word_id,))
    word = cursor.fetchone()

    conn.close()
    return word

@st.experimental_memo(ttl=3600)
def fetch_words_from_api(api_url):
    response = requests.get(f"{api_url}/words?page=1")
    if response.status_code == 200:
        return response.json().get('words', [])
    else:
        st.error("Failed to fetch words from the API.")
        return []

def fetch_word_collection(source, db_path=None, api_url=None):
    if source == 'db' and db_path:
        return fetch_words_from_db(db_path)
    elif source == 'api' and api_url:
        return fetch_words_from_api(api_url)
    else:
        st.error("Invalid source or missing parameters.")
        return []

app = Flask(__name__)

@app.route('/words', methods=['GET'])
@cross_origin()
def get_words():
    try:
        db_path = 'path_to_your_db'
        page = int(request.args.get('page', 1))
        sort_by = request.args.get('sort_by', 'jiantizi')
        order = request.args.get('order', 'asc')

        words, total_pages, total_words = fetch_words_from_db(db_path, page, sort_by=sort_by, order=order)

        words_data = []
        for word in words:
            words_data.append({
                "id": word[0],
                "jiantizi": word[1],
                "pinyin": word[2],
                "english": word[3],
                "correct_count": word[4],
                "wrong_count": word[5]
            })

        return jsonify({
            "words": words_data,
            "total_pages": total_pages,
            "current_page": page,
            "total_words": total_words
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/words/<int:word_id>', methods=['GET'])
@cross_origin()
def get_word(word_id):
    try:
        db_path = 'path_to_your_db'
        word = fetch_word_from_db(db_path, word_id)

        if not word:
            return jsonify({"error": "Word not found"}), 404

        groups = []
        if word[6]:
            for group_str in word[6].split(','):
                group_id, group_name = group_str.split('::')
                groups.append({
                    "id": int(group_id),
                    "name": group_name
                })

        return jsonify({
            "word": {
                "id": word[0],
                "jiantizi": word[1],
                "pinyin": word[2],
                "english": word[3],
                "correct_count": word[4],
                "wrong_count": word[5],
                "groups": groups
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)