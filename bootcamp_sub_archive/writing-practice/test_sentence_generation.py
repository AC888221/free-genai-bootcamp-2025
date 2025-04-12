# test_sentence_generation.py

import pytest
import requests
from unittest.mock import patch, Mock
from backend.sentence_generation import generate_sentence, store_sentence

@pytest.fixture
def setup_session_state():
    import streamlit as st
    st.session_state['current_state'] = 'setup'
    st.session_state['word_collection'] = []
    st.session_state['current_sentence'] = {}
    st.session_state['grading_results'] = {}

def test_generate_sentence_success(setup_session_state):
    api_url = 'http://example.com/api'
    group_id = 'test_group'
    _word = '书'
    
    with patch('backend.sentence_generation.call_claude_haiku') as mock_call:
        mock_call.return_value = '{"english": "I read a book", "chinese": "我读了一本书", "pinyin": "wǒ dú le yī běn shū"}'
        sentence_data = generate_sentence(api_url, group_id, _word)
        assert sentence_data['english'] == "I read a book"
        assert sentence_data['chinese'] == "我读了一本书"
        assert sentence_data['pinyin'] == "wǒ dú le yī běn shū"

def test_generate_sentence_fallback_no_json(setup_session_state):
    api_url = 'http://example.com/api'
    group_id = 'test_group'
    _word = '书'
    
    with patch('backend.sentence_generation.call_claude_haiku') as mock_call:
        mock_call.return_value = 'Some explanation without JSON'
        sentence_data = generate_sentence(api_url, group_id, _word)
        assert sentence_data['english'] == "I want to learn Chinese"
        assert sentence_data['chinese'] == "我想学中文"
        assert sentence_data['pinyin'] == "wǒ xiǎng xué zhōngwén"

def test_generate_sentence_error_handling(setup_session_state):
    api_url = 'http://example.com/api'
    group_id = 'test_group'
    _word = '书'
    
    with patch('backend.sentence_generation.call_claude_haiku') as mock_call:
        mock_call.side_effect = Exception("API error")
        sentence_data = generate_sentence(api_url, group_id, _word)
        assert sentence_data['english'] == "I want to learn Chinese"
        assert sentence_data['chinese'] == "我想学中文"
        assert sentence_data['pinyin'] == "wǒ xiǎng xué zhōngwén"

def test_store_sentence_success():
    api_url = 'http://example.com/api'
    group_id = 'test_group'
    sentence_data = {
        "english": "I read a book",
        "chinese": "我读了一本书",
        "pinyin": "wǒ dú le yī běn shū"
    }
    
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response
        store_sentence(api_url, group_id, sentence_data)
        mock_post.assert_called_once_with(f"{api_url}/groups/{group_id}/sentences", json=sentence_data)

def test_store_sentence_failure():
    api_url = 'http://example.com/api'
    group_id = 'test_group'
    sentence_data = {
        "english": "I read a book",
        "chinese": "我读了一本书",
        "pinyin": "wǒ dú le yī běn shū"
    }
    
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        store_sentence(api_url, group_id, sentence_data)
        mock_post.assert_called_once_with(f"{api_url}/groups/{group_id}/sentences", json=sentence_data)