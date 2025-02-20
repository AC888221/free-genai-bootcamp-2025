# Lang Portal

A language learning portal supporting:
- Simplified Chinese characters (jiantizi)
- Pinyin with tone marks
- English translations

## Features

- Chinese character display with pinyin pronunciation
- Pinyin input with tone number support (e.g., "ni3 hao3" -> "nǐ hǎo")
- Study sessions with progress tracking
- Word grouping and review system

## Setup

### Frontend Requirements
- Noto Sans SC font (for Chinese characters)
- Source Sans Pro font (for pinyin display)

### Backend Requirements
- SQLite3 with UTF-8 support
- Python 3.8+
- Node.js 14+

See individual README files in frontend-react/ and backend-flask/ for detailed setup instructions.

## Install

```sh
pip install -r requirements.txt
```

## Setup DB

```
invoke init-db
```

## Run

```sh
python app.py
```