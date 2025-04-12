# Technical Specs - Putonghua Language Learning App (Streamlit)

## Setup & Dependencies
- Create a Streamlit application using `streamlit` library
- Required Python packages:
  - `streamlit`
  - `requests` (for API calls)
  - `pillow` (for image processing)
  - `pandas` (for data handling)
  - `langchain` or equivalent (for LLM integration)
  - A Chinese OCR library (e.g., `PaddleOCR` or `EasyOCR`)
  - `streamlit-extras` (optional, for enhanced UI components)
  - `gtts` (for text-to-speech capabilities)

## Initialization Step
When the Streamlit app initializes it needs to do the following:
- Fetch from `GET localhost:5000/api/groups/:id/raw` using `requests`, which will return a collection of words in a JSON structure containing Putonghua (Mandarin Chinese) words with their English translations
- Store this collection of words in a Streamlit session state using `st.session_state`
- Initialize audio capabilities for pronunciation support using `st.audio`

## App States & UI Flow
Using Streamlit's stateful design pattern with `st.session_state['current_state']` to manage app states.

### Setup State
When a user first loads the Streamlit app:
- Display a centered title using `st.title("Putonghua Practice")`
- Add a brief introduction with `st.markdown()`
- Display a prominent "Generate Sentence" button using `st.button()`
- When the button is clicked:
  - Randomly select a word from the fetched collection
  - Call the Sentence Generator LLM
  - Set `st.session_state['current_state'] = 'practice'`
  - Store generated sentence data in session state
  - Trigger a rerun with `st.experimental_rerun()`

### Practice State
When `st.session_state['current_state'] == 'practice'`:
- Display the English sentence using `st.subheader()`
- Show a toggle for Pinyin display using `st.checkbox()`
- Conditionally display Pinyin with `st.markdown()` if checkbox is selected
- Add an audio playback widget using `st.audio()` with generated TTS
- Create a file uploader for images using `st.file_uploader(accept_multiple_files=False, type=['png', 'jpg', 'jpeg'])`
- Display a "Submit for Review" button using `st.button()` (disabled until image is uploaded)
- When the button is clicked:
  - Save the uploaded image temporarily
  - Pass the image to the Grading System
  - Set `st.session_state['current_state'] = 'review'`
  - Store grading results in session state
  - Trigger a rerun with `st.experimental_rerun()`

### Review State
When `st.session_state['current_state'] == 'review'`:
- Display the original English sentence using `st.subheader()`
- Display the user's submitted image using `st.image()`
- Create a results section with `st.expander("Review Results", expanded=True)`
- Inside the expander, show:
  - Character-by-character transcription using `st.code()`
  - Translation back to English using `st.markdown()`
  - Grade visualization with `st.progress()` and letter grade with `st.metric()`
  - Feedback and suggestions using `st.markdown()`
  - Side-by-side comparison of user characters vs. correct characters
- Add "Try Again" and "New Sentence" buttons using `st.button()` in `st.columns()`
- Handle button clicks to either reset current sentence or generate a new one

## Sentence Generator LLM Integration
Implement a function that:
- Takes a random word from the collection
- Uses an LLM API (via langchain or direct API calls) with the following prompt template:
Generate a simple sentence using the following word: {{word}}
The grammar should be scoped to HSK Level 1-2 grammar patterns.
You can use the following vocabulary to construct a simple sentence:

Common objects (e.g., book/书, water/水, food/食物)
Basic verbs (e.g., to eat/吃, to drink/喝, to go/去)
Simple time expressions (e.g., today/今天, tomorrow/明天, yesterday/昨天)

Return the following in JSON format:
{
"english": "The English sentence",
"chinese": "The Chinese sentence in simplified characters",
"pinyin": "The pinyin representation with tone marks"
}

- Parses the JSON response and stores it in `st.session_state`
- Generates audio file for the Chinese sentence using `gtts` and stores the audio data

## Grading System Implementation
Create a module that:
- Takes the uploaded image and processes it using Pillow
- Passes the processed image to a Chinese OCR system (PaddleOCR or EasyOCR)
- Makes an LLM call to translate the transcription back to English
- Makes another LLM call to grade the submission with the following context:
- The original English sentence
- The expected Chinese characters
- The transcribed characters from the user's image
- The back-translation to English
- Returns a structured result containing:
- The transcription
- The back-translation
- The letter grade (S/A/B/C/D)
- Character-by-character feedback
- Improvement suggestions

## Caching Strategy
- Use `@st.cache_data` decorator for:
- API requests to fetch word collection
- LLM calls for sentence generation
- OCR processing functions
- Use `@st.cache_resource` for:
- OCR model initialization
- LLM client initialization

## Deployment Notes
- Package requirements in `requirements.txt`
- Set up environment variables for API keys and endpoints
- Can be deployed on Streamlit Cloud, Heroku, or any platform supporting Python web apps
- Local development can be run using `streamlit run app.py`