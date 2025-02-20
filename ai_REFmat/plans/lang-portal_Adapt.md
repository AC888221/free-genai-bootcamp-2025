# Lang-Portal Adaptation Plan: Japanese to Mandarin Chinese (Jiantizi)

## Overview of Changes

### Database Schema Changes
1. ✅ Rename columns in `words` table
   - Change `kanji` to `jiantizi`
   - Change `romaji` to `pinyin`
   ```sql
   ALTER TABLE words RENAME COLUMN kanji TO jiantizi;
   ALTER TABLE words RENAME COLUMN romaji TO pinyin;
   ```

### Backend Changes (backend-flask)

2. ✅ Update routes/words.py
   ```python
   # Change response structure
   return jsonify({
       'id': word['id'],
       'jiantizi': word['jiantizi'],  # Previously kanji
       'pinyin': word['pinyin'],      # Previously romaji
       'english': word['english']
   })
   ```

3. ✅ Update routes/study_sessions.py
   ```python
   # Update SQL queries
   cursor.execute('''
       SELECT w.*
       FROM words w
       JOIN word_review_items wri ON wri.word_id = w.id
       WHERE wri.study_session_id = ?
       ORDER BY w.jiantizi  # Previously w.kanji
   ''', (id,))
   ```

4. ✅ Update routes/groups.py
   ```python
   # Update sort parameters
   valid_columns = ['jiantizi', 'pinyin', 'english']  # Previously kanji, romaji
   ```

### Frontend Changes (frontend-react)

5. ✅ Update API interfaces (src/api/types.ts)
   ```typescript
   interface Word {
     id: number;
     jiantizi: string;     // Previously kanji
     pinyin: string;       // Previously romaji
     english: string;
   }
   ```

6. ✅ Update components displaying words
   ```typescript
   // src/components/WordCard.tsx
   const WordCard: React.FC<{ word: Word }> = ({ word }) => {
     return (
       <div className="word-card">
         <h2 className="chinese-character">{word.jiantizi}</h2>
         <p className="pinyin">{word.pinyin}</p>
         <p className="english">{word.english}</p>
       </div>
     );
   };
   ```

### Font and Display Updates

7. ✅ Update font configurations
   ```css
   /* styles.css */
   .chinese-character {
     /* Noto Sans SC is optimized for simplified Chinese */
     font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
     font-size: 2em;
   }
   
   .pinyin {
     font-family: "Source Sans Pro", sans-serif;
     font-size: 1.2em;
   }
   ```

### Testing Plan

8. ✅ Database Testing
    ```sql
    -- Test data insertion with simplified characters
    INSERT INTO words (jiantizi, pinyin, english) 
    VALUES ('学习', 'xué xí', 'study');
    
    -- Verify correct encoding and storage
    SELECT * FROM words WHERE jiantizi = '学习';
    ```

9. ✅ API Testing
    ```bash
    # Test word creation
    curl -X POST http://localhost:5000/api/words \
      -H "Content-Type: application/json" \
      -d '{
        "jiantizi": "学习",
        "pinyin": "xué xí",
        "english": "study"
      }'
    ```

10. ✅ Component Testing
    ```typescript
    // src/__tests__/WordCard.test.tsx
    test('renders simplified Chinese characters correctly', () => {
      const word = {
        id: 1,
        jiantizi: '学习',
        pinyin: 'xué xí',
        english: 'study'
      };
      
      render(<WordCard word={word} />);
      expect(screen.getByText('学习')).toBeInTheDocument();
    });
    ```

### Pinyin Support

11. ✅ Add tone mark support
    ```typescript
    // src/utils/pinyinUtils.ts
    const pinyinTonesMap = {
      'a': ['a', 'ā', 'á', 'ǎ', 'à'],
      'e': ['e', 'ē', 'é', 'ě', 'è'],
      // ... other vowels
    };
    
    export const addToneMarks = (pinyin: string, tone: number): string => {
      // Implementation for converting numbered pinyin to tone marks
    };
    ```

12. ✅ Add pinyin input helper
    ```typescript
    // src/components/PinyinInput.tsx
    const PinyinInput: React.FC<{ onChange: (value: string) => void }> = ({ onChange }) => {
      const [rawInput, setRawInput] = useState('');
      
      const handleInput = (input: string) => {
        // Convert numbered pinyin (e.g., "ni3") to tone marks (e.g., "nǐ")
        const withTones = convertNumberedPinyinToTones(input);
        onChange(withTones);
      };
      
      return <input onChange={(e) => handleInput(e.target.value)} />;
    };
    ```

### Documentation Updates

13. ✅ Update API documentation
    ```markdown
    ## Word Object
    
    - `jiantizi` (string): The simplified Chinese character(s)
    - `pinyin` (string): The romanized pronunciation with tone marks
    - `english` (string): English translation
    ```

14. ✅ Add Chinese-specific guidelines
    ```markdown
    ### Pinyin Guidelines
    
    - Always include tone marks
    - Separate syllables with spaces
    - Use v for ü (e.g., "nv3" for "nǚ")
    
    ### Character Guidelines
    
    - Use simplified Chinese characters (简体字)
    - Verify characters against GB2312 standard
    ```

### Final Verification

15. ✅ Character encoding verification
    - Test database storage and retrieval
    - Verify API response encoding
    - Check character rendering in UI
    - Verify search functionality with both characters and pinyin

16. ✅ Pinyin verification
    - Test tone mark display
    - Verify pinyin input conversion
    - Check pinyin search functionality
    - Verify sorting by pinyin

### Deployment Checklist

17. ✅ Pre-deployment tasks
    - Backup existing data
    - Prepare database migration scripts
    - Update character encoding settings
    - Test in staging environment

18. ✅ Post-deployment verification
    - Verify character display
    - Check pinyin tone marks
    - Test search functionality
    - Monitor error logs for encoding issues

### Unit Tests

19. ✅ Add specific tests for Chinese character handling
    ```typescript
    // src/__tests__/ChineseUtils.test.ts
    describe('Chinese character handling', () => {
      test('correctly displays simplified characters', () => {
        const text = '你好';
        expect(renderChineseText(text)).toBeTruthy();
      });
    
      test('converts numbered pinyin to tone marks', () => {
        expect(convertPinyin('ni3 hao3')).toBe('nǐ hǎo');
      });
    });
    ```

20. ✅ Add API endpoint tests
    ```python
    # tests/test_api.py
    def test_word_creation():
        response = client.post('/api/words', json={
            'jiantizi': '你好',
            'pinyin': 'nǐ hǎo',
            'english': 'hello'
        })
        assert response.status_code == 201
        assert 'jiantizi' in response.json
    ```