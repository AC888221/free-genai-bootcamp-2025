# Writing Practice

A Streamlit-based application for practicing Chinese (Putonghua) writing with AI-powered feedback using Claude 3 Haiku.

## Documentation

- [📸 Application Showcase](./Showcase_writing-practice.md) - Visual tour of features and user experience
- [📝 Implementation Details](./IMPLEMENTATION.md) - Technical implementation report
- [🏠 Main Project Documentation](../../README.md) - Main project overview

## Technical Overview

This application provides:
- Chinese character practice with OCR-based recognition
- AI-powered sentence generation and feedback
- Text-to-speech audio support
- Image processing for handwriting analysis

## System Requirements

### Required System Dependencies

1. **Tesseract OCR** - Required for character recognition
   
   For Ubuntu/Debian:
   ```bash
   sudo apt-get update
   sudo apt-get install tesseract-ocr
   sudo apt-get install tesseract-ocr-chi-sim  # For Chinese support
   ```
   
   For Windows:
   1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
   2. Run the installer
   3. Add Tesseract to your PATH environment variable
   
   For macOS:
   ```bash
   brew install tesseract
   brew install tesseract-lang  # For language support
   ```

   Verify installation:
   ```bash
   tesseract --version
   ```

## Project Structure

```
writing-practice/
├── app.py                 # Main Streamlit application
├── config.py             # Configuration settings
├── frontend/
│   ├── styling.py        # CSS and UI styling
│   └── state_management.py # Session state management
├── backend/
│   ├── ocr_reader.py     # OCR initialization
│   ├── bedrock_client.py # AWS Bedrock setup
│   ├── claude_haiku.py   # Claude API integration
│   ├── word_collection.py # Vocabulary management
│   ├── sentence_generation.py # Sentence creation
│   ├── audio_generation.py # Text-to-speech
│   └── image_processing.py # Image analysis
├── requirements.txt      # Python dependencies
└── .gitignore           # Git ignore rules
```

## Installation

1. Install system dependencies (see System Requirements above)

2. Clone the repository:
```bash
git clone https://github.com/yourusername/writing-practice.git
cd writing-practice
```

3. Create and activate a virtual environment:
```bash
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate
```

4. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Set up AWS credentials via environment variables:
```bash
export AWS_ACCESS_KEY_ID='your_access_key'
export AWS_SECRET_ACCESS_KEY='your_secret_key'
export AWS_DEFAULT_REGION='your_region'
```

2. Launch the Lang Portal backend service:
```bash
cd path/to/lang-portal/backend-flask
python app.py
```

3. Start the Writing Practice app:
```bash
cd path/to/writing-practice
streamlit run app.py
```

## Technical Requirements

- Python 3.8+
- Tesseract OCR with Chinese language support
- Core Dependencies:
  - numpy==1.26.0
  - pandas==2.1.1
  - streamlit==1.27.0
  - pytesseract==0.3.13
- API Dependencies:
  - flask==2.3.3
  - flask-cors==4.0.0
- Image Processing:
  - Pillow==9.5.0
- Audio Processing:
  - gtts==2.3.2
- AWS Integration:
  - boto3==1.28.62
  - botocore>=1.31.62

## Troubleshooting

### Common Issues

1. **OCR Not Working**
   - Verify Tesseract is installed: `tesseract --version`
   - Check Chinese language support: `tesseract --list-langs`
   - Ensure image is clear and well-lit

2. **Image Processing Errors**
   - Confirm image format is supported (PNG, JPEG, BMP)
   - Check image resolution and size
   - Ensure proper lighting and contrast in handwriting

3. **Connection Issues**
   - Verify Lang Portal is running on port 5000
   - Check AWS credentials are properly set
   - Ensure network connectivity for API calls

## Development Notes

### Domain Knowledge and Technical Implementation

[See the full technical implementation report in IMPLEMENTATION.md]

### Image Processing Pipeline
- Format validation and conversion
- Contrast enhancement
- Noise reduction
- Size normalization

### Performance Optimization
- Response caching
- Memory management
- Async operations

### Error Handling
- Input validation
- OCR quality checks
- Graceful degradation
- API retry mechanisms

