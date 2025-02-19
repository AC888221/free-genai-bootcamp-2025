# API Fix Plan

## 1. study_sessions.py Fixes

### Route Path Fixes
1. ✅ Update route paths to include `/api` prefix consistently
   - Change `/study-sessions` to `/api/study-sessions` for all routes
   - Test each route with updated paths using curl or Postman

---

### Missing Endpoint Implementation
2. ✅ Implement missing POST `/api/study-sessions/:id/review` endpoint

\```python
@app.route('/api/study-sessions/<id>/review', methods=['POST'])
@cross_origin()
def create_study_session_review(id):
    try:
        data = request.get_json()
        if not data or not all(key in data for key in ('word_id', 'correct')):
            return jsonify({"error": "Missing required fields"}), 400
        cursor = app.db.cursor()
        cursor.execute('''
            INSERT INTO word_review_items (word_id, study_session_id, correct, created_at)
            VALUES (?, ?, ?, datetime('now'))
        ''', (data['word_id'], id, data['correct']))
        app.db.commit()
        return jsonify({"message": "Review recorded successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
\```

---

### Testing Steps
3. ✅ Test study session creation:

\```bash
curl -X POST http://localhost:5000/api/study-sessions \
-H "Content-Type: application/json" \
-d '{"group_id": 1, "study_activity_id": 1, "created_at": "2024-03-20T12:00:00Z"}'
\```

---

4. ✅ Test study session review:

\```bash
curl -X POST http://localhost:5000/api/study-sessions/1/review \
-H "Content-Type: application/json" \
-d '{"word_id": 1, "correct": true}'
\```

---

5. ✅ Test study session retrieval:

\```bash
curl http://localhost:5000/api/study-sessions/1
\```

---

## 2. groups.py Fixes

### Route Path Standardization
1. ✅ Update route paths to include `/api` prefix
   - Change `/groups` to `/api/groups` for all routes
   - Update all related routes to maintain consistency

---

### Missing Endpoint Implementation
2. ✅ Implement GET `/api/groups/:id/words/raw` endpoint

\```python
@app.route('/api/groups/<int:id>/words/raw', methods=['GET'])
@cross_origin()
def get_group_words_raw(id):
    try:
        cursor = app.db.cursor()
        cursor.execute('''
            SELECT w.*
            FROM words w
            JOIN word_groups wg ON w.id = wg.word_id
            WHERE wg.group_id = ?
            ORDER BY w.kanji
        ''', (id,))
        words = cursor.fetchall()
        return jsonify([{
            "id": word["id"],
            "kanji": word["kanji"],
            "romaji": word["romaji"],
            "english": word["english"]
        } for word in words])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
\```

---

### Testing Steps
3. ✅ Test group listing:

\```bash
curl http://localhost:5000/api/groups
\```

---

4. ✅ Test group details:

\```bash
curl http://localhost:5000/api/groups/1
\```

---

5. ✅ Test group words (raw):

\```bash
curl http://localhost:5000/api/groups/1/words/raw
\```

---

## Frontend API Link Verification

1. ✅ Check frontend API configuration file (likely in `src/config` or `src/api`)
   - Update all API endpoints to include `/api` prefix
   - Verify all endpoint paths match the backend routes

---

2. ✅ Search for direct API calls in components:

\```bash
grep -r "fetch(" ./src
grep -r "axios" ./src
\```

---

3. ✅ Update any hardcoded API URLs found in components to match new routes

---

4. ✅ Test frontend functionality:
   - Test group listing page
   - Test study session creation
   - Test word review submission
   - Test study session history viewing

---

## Unit Tests

Create a new test file `test_api.py`:
\```python
import unittest
import json
from app import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_create_study_session(self):
        response = self.app.post('/api/study-sessions',
                                 json={
                                     'group_id': 1,
                                     'study_activity_id': 1,
                                     'created_at': '2024-03-20T12:00:00Z'
                                 })
        self.assertEqual(response.status_code, 201)

    def test_create_review(self):
        response = self.app.post('/api/study-sessions/1/review',
                                 json={
                                     'word_id': 1,
                                     'correct': True
                                 })
        self.assertEqual(response.status_code, 201)

    def test_get_groups(self):
        response = self.app.get('/api/groups')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('groups', data)

if __name__ == '__main__':
    unittest.main()
\```

---

Run tests with:

\```bash
python -m unittest test_api.py
\```

---

Remember to:
- ✅ Back up files before making changes
- ✅ Test each endpoint after modifications
- ✅ Update API documentation after changes
- ✅ Verify frontend compatibility