### Routes

#### GET /words
- Get a paginated list of words with review statistics.

#### GET /groups
- Get a paginated list of word groups with word counts.

#### GET /groups/:id
- Get words from a specific group (this is intended to be used by target apps).

#### POST /study_sessions
- Create a new study session for a group.

#### POST /study_sessions/:id/review
- Log a review attempt for a word during a study session.

#### GET /words
- `page`: Page number (default: 1).
- `sort_by`: Sort field ('kanji', 'romaji', 'english', 'correct_count', 'wrong_count') (default: 'kanji').
- `order`: Sort order ('asc' or 'desc') (default: 'asc').

#### GET /groups/:id
- `page`: Page number (default: 1).
- `sort_by`: Sort field ('name', 'words_count') (default: 'name').
- `order`: Sort order ('asc' or 'desc') (default: 'asc').

#### POST /study_sessions
- `group_id`: ID of the group to study (required).
- `study_activity_id`: ID of the study activity (required).

#### POST /study_sessions/:id/review

### Database Schema

#### words — Stores individual Japanese vocabulary words.
- `id` (Primary Key): Unique identifier for each word.
- `kanji` (String, required): The word written in Japanese kanji.
- `romaji` (String, required): Romanized version of the word.
- `english` (String, required): English translation of the word.
- `parts` (JSON, required): Word components stored in JSON format.

#### groups — Manages collections of words.
- `id` (Primary Key): Unique identifier for each group.
- `name` (String, required): Name of the group.
- `words_count` (Integer, default: 0): Counter cache for the number of words in the group.

#### word_groups — Join-table enabling many-to-many relationship between words and groups.
- `word_id` (Foreign Key): References words.id.
- `group_id` (Foreign Key): References groups.id.

#### study_activities — Defines different types of study activities available.
- `id` (Primary Key): Unique identifier for each activity.
- `name` (String, required): Name of the activity (e.g., "Flashcards", "Quiz").
- `url` (String, required): The full URL of the study activity.

#### study_sessions — Records individual study sessions.
- `id` (Primary Key): Unique identifier for each session.
- `group_id` (Foreign Key): References groups.id.
- `study_activity_id` (Foreign Key): References study_activities.id.
- `created_at` (Timestamp, default: current time): When the session was created.

#### word_review_items — Tracks individual word reviews within study sessions.
- `id` (Primary Key): Unique identifier for each review.
- `word_id` (Foreign Key): References words.id.
- `study_session_id` (Foreign Key): References study_sessions.id.
- `correct` (Boolean, required): Whether the answer was correct.
- `created_at` (Timestamp, default: current time): When the review occurred.

### Relationships

- A word belongs to groups through `word_groups`.
- A group belongs to words through `word_groups`.
- A session belongs to a group.
- A session belongs to a study_activity.
- A session has many `word_review_items`.
- A `word_review_item` belongs to a study_session.
- A `word_review_item` belongs to a word.