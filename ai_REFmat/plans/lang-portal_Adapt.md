# Lang-Portal Adaptation Plan: Japanese to Mandarin Chinese

## Overview of Changes

### Database Schema Changes
1. ✅ Rename columns in `words` table
   - Change `kanji` to `hanzi`
   - Change `romaji` to `pinyin`
   ```sql
   ALTER TABLE words RENAME COLUMN kanji TO hanzi;
   ALTER TABLE words RENAME COLUMN romaji TO pinyin;
   ```

2. ✅ Update existing database triggers and functions
   ```sql
   -- Update any triggers that reference these columns
   CREATE OR REPLACE TRIGGER update_word_trigger
   BEFORE UPDATE ON words
   FOR EACH ROW
   BEGIN
     -- Update trigger logic for hanzi/pinyin
   END;
   ```

### Backend Changes (backend-flask)

3. ✅ Update routes/words.py
   ```python
   # Change response structure
   return jsonify({
       'id': word['id'],
       'hanzi': word['hanzi'],  # Previously kanji
       'pinyin': word['pinyin'],  # Previously romaji
       'english': word['english']
   })
   ```

4. ✅ Update routes/study_sessions.py
   ```python
   # Update SQL queries
   cursor.execute('''
       SELECT w.*
       FROM words w
       JOIN word_review_items wri ON wri.word_id = w.id
       WHERE wri.study_session_id = ?
       ORDER BY w.hanzi  # Previously w.kanji
   ''', (id,))
   ```

5. ✅ Update routes/groups.py
   ```python
   # Update sort parameters
   valid_columns = ['hanzi', 'pinyin', 'english']  # Previously kanji, romaji
   ```

### Frontend Changes (frontend-react)

6. ✅ Update API interfaces (src/api/types.ts)
   ```typescript
   interface Word {
     id: number;
     hanzi: string;  // Previously kanji
     pinyin: string;  // Previously romaji
     english: string;
   }
   ```

7. ✅ Update components displaying words
   ```typescript
   // src/components/WordCard.tsx
   const WordCard: React.FC<{ word: Word }> = ({ word }) => {
     return (
       <div className="word-card">
         <h2>{word.hanzi}</h2>
         <p>{word.pinyin}</p>
         <p>{word.english}</p>
       </div>
     );
   };
   ```

8. ✅ Update sort options in list views
   ```typescript
   // src/components/WordList.tsx
   const sortOptions = [
     { value: 'hanzi', label: 'Sort by Character' },
     { value: 'pinyin', label: 'Sort by Pinyin' },
     { value: 'english', label: 'Sort by English' }
   ];
   ```

### Testing Plan

9. ✅ Database Migration Testing
   ```sql
   -- Test data for verification
   INSERT INTO words (hanzi, pinyin, english) 
   VALUES ('你好', 'nǐhǎo', 'hello');
   
   -- Verify insertion
   SELECT * FROM words WHERE hanzi = '你好';
   ```

10. ✅ Backend API Testing
    ```bash
    # Test word retrieval
    curl http://localhost:5000/api/words/1 | jq
    
    # Test word creation
    curl -X POST http://localhost:5000/api/words \
      -H "Content-Type: application/json" \
      -d '{"hanzi": "你好", "pinyin": "nǐhǎo", "english": "hello"}'
    ```

11. ✅ Frontend Component Testing
    ```typescript
    // src/__tests__/WordCard.test.tsx
    import { render, screen } from '@testing-library/react';
    import WordCard from '../components/WordCard';

    test('renders word card with Chinese characters', () => {
      const word = {
        id: 1,
        hanzi: '你好',
        pinyin: 'nǐhǎo',
        english: 'hello'
      };
      
      render(<WordCard word={word} />);
      
      expect(screen.getByText('你好')).toBeInTheDocument();
      expect(screen.getByText('nǐhǎo')).toBeInTheDocument();
      expect(screen.getByText('hello')).toBeInTheDocument();
    });
    ```

### UI/UX Updates

12. ✅ Update labels and placeholders
    - Change "Kanji" to "Hanzi" in all UI elements
    - Change "Romaji" to "Pinyin" in all UI elements
    - Update placeholder text in search inputs

13. ✅ Update CSS classes and styles
    ```css
    /* Update class names for clarity */
    .hanzi-text {  /* Previously .kanji-text */
      font-size: 2em;
      font-family: "Noto Sans SC", sans-serif;  /* Chinese font */
    }
    
    .pinyin-text {  /* Previously .romaji-text */
      font-size: 1.2em;
      color: #666;
    }
    ```

### Documentation Updates

14. ✅ Update API documentation
    - Update all endpoint descriptions
    - Update request/response examples
    - Update field descriptions

15. ✅ Update README.md
    - Update project description
    - Update setup instructions
    - Update example data

### Final Verification

16. ✅ End-to-end testing
    - Test word creation flow
    - Test study session creation
    - Test word review functionality
    - Verify sorting and filtering
    - Check character display in all views

17. ✅ Performance testing
    - Verify database query performance with Chinese characters
    - Check frontend rendering performance
    - Test search functionality with pinyin input

### Deployment Steps

18. ✅ Prepare deployment
    - Back up existing database
    - Create database migration scripts
    - Update environment variables if needed
    - Update build scripts

19. ✅ Post-deployment verification
    - Verify all API endpoints
    - Check database encoding
    - Verify frontend functionality
    - Monitor error logs

## Additional Notes

- Ensure proper UTF-8 encoding throughout the application
- Consider adding pinyin tone mark support
- Consider adding traditional Chinese character support (fantizi) as an option
- Update any third-party integrations that might depend on Japanese-specific features