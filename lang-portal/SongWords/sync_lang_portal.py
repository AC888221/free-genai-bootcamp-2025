import requests
from database import Database
from typing import Dict, List
import logging
from config import LANG_PORTAL_URL, DB_PATH, SEARCH_CONFIG, LOG_CONFIG

logger = logging.getLogger(__name__)

class LangPortalSync:
    def __init__(self, lang_portal_url: str = None):
        # Use configured URL as default, allow override for testing
        self.lang_portal_url = lang_portal_url or LANG_PORTAL_URL
        self.db = Database(DB_PATH)

    def get_lang_portal_words(self) -> Dict[str, dict]:
        """Fetch all words from lang-portal and index them by jiantizi."""
        all_words = {}
        page = 1
        retries = 0
        
        while True:
            try:
                response = requests.get(
                    f"{self.lang_portal_url}/words", 
                    params={"page": page},
                    timeout=SEARCH_CONFIG["timeout"]
                )
                if response.status_code != 200:
                    if retries < SEARCH_CONFIG["max_retries"]:
                        retries += 1
                        continue
                    raise Exception(f"Failed to fetch words from lang-portal: {response.text}")
                
                data = response.json()
                if not data["words"]:
                    break
                    
                for word in data["words"]:
                    all_words[word["jiantizi"]] = word
                
                if page >= data["total_pages"]:
                    break
                page += 1
                retries = 0  # Reset retries on successful request
                
            except requests.Timeout:
                if retries < SEARCH_CONFIG["max_retries"]:
                    retries += 1
                    continue
                raise Exception("Request timed out while fetching words from lang-portal")
                
        return all_words

    def resolve_conflict(self, songwords_word: dict, lang_portal_word: dict) -> dict:
        """
        Resolve conflicts between two versions of the same word.
        Returns the resolved version.
        """
        # If lang_portal version has review counts, prefer it but update translations
        if lang_portal_word.get("correct_count", 0) > 0 or lang_portal_word.get("wrong_count", 0) > 0:
            resolved = lang_portal_word.copy()
            # Only update translations if SongWords has non-empty values
            if songwords_word["pinyin"] and not lang_portal_word["pinyin"]:
                resolved["pinyin"] = songwords_word["pinyin"]
            if songwords_word["english"] and not lang_portal_word["english"]:
                resolved["english"] = songwords_word["english"]
            return resolved
        
        # If no review history, prefer the more complete entry
        songwords_completeness = sum(1 for v in songwords_word.values() if v)
        lang_portal_completeness = sum(1 for v in lang_portal_word.values() if v)
        
        return songwords_word if songwords_completeness >= lang_portal_completeness else lang_portal_word

    def sync_to_lang_portal(self) -> Dict[str, int]:
        """
        Sync words from SongWords to lang-portal.
        Returns statistics about the sync operation.
        """
        stats = {"added": 0, "updated": 0, "skipped": 0, "errors": 0}
        retries = 0
        
        try:
            # Get all words from both systems
            songwords_vocab = self.db.get_all_unique_vocabulary()
            lang_portal_words = self.get_lang_portal_words()
            
            for word in songwords_vocab:
                try:
                    if word["jiantizi"] not in lang_portal_words:
                        # Add new word to lang-portal
                        response = requests.post(
                            f"{self.lang_portal_url}/words",
                            json=word,
                            timeout=SEARCH_CONFIG["timeout"]
                        )
                        if response.status_code == 201:
                            stats["added"] += 1
                        else:
                            if retries < SEARCH_CONFIG["max_retries"]:
                                retries += 1
                                continue
                            stats["errors"] += 1
                            logger.error(f"Failed to add word {word['jiantizi']}: {response.text}")
                    else:
                        # Handle potential conflicts
                        existing_word = lang_portal_words[word["jiantizi"]]
                        resolved_word = self.resolve_conflict(word, existing_word)
                        
                        if resolved_word != existing_word:
                            response = requests.put(
                                f"{self.lang_portal_url}/words/{existing_word['id']}",
                                json=resolved_word,
                                timeout=SEARCH_CONFIG["timeout"]
                            )
                            if response.status_code == 200:
                                stats["updated"] += 1
                            else:
                                if retries < SEARCH_CONFIG["max_retries"]:
                                    retries += 1
                                    continue
                                stats["errors"] += 1
                                logger.error(f"Failed to update word {word['jiantizi']}: {response.text}")
                        else:
                            stats["skipped"] += 1
                            retries = 0  # Reset retries on successful operation
                            
                except requests.Timeout:
                    if retries < SEARCH_CONFIG["max_retries"]:
                        retries += 1
                        continue
                    stats["errors"] += 1
                    logger.error(f"Timeout processing word {word['jiantizi']}")
                except Exception as e:
                    stats["errors"] += 1
                    logger.error(f"Error processing word {word['jiantizi']}: {str(e)}")
                    
            return stats
            
        except Exception as e:
            logger.error(f"Sync failed: {str(e)}")
            raise