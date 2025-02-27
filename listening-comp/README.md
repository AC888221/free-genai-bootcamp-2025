# Language Learning Assistant (LLA)
This is for the generative AI bootcamp

[Jump to Bootcamp Week 2: LLA Implementation Report](https://github.com/AC888221/free-genai-bootcamp-2025/blob/main/language-learning-assistant-main/README.md#bootcamp-week-2-lla-implementation-report)

**Difficulty:** Level 200 *(Due to RAG implementation and multiple AWS services integration)*

**Business Goal:**
A progressive learning tool that demonstrates how RAG and agents can enhance language learning by grounding responses in real Japanese lesson content. The system shows the evolution from basic LLM responses to a fully contextual learning assistant, helping students understand both the technical implementation and practical benefits of RAG.

**Technical Uncertainty:**
1. How effectively can we process and structure bilingual (Japanese/English) content for RAG?
2. What's the optimal way to chunk and embed Japanese language content?
3. How can we effectively demonstrate the progression from base LLM to RAG to students?
4. Can we maintain context accuracy when retrieving Japanese language examples?
5. How do we balance between giving direct answers and providing learning guidance?
6. What's the most effective way to structure multiple-choice questions from retrieved content?

**Technical Restrictions:**
* Must use Amazon Bedrock for:
   * API (converse, guardrails, embeddings, agents) (https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
     * Aamzon Nova Micro for text generation (https://aws.amazon.com/ai/generative-ai/nova)
   * Titan for embeddings
* Must implement in Streamlit, pandas (data visualization)
* Must use SQLite for vector storage
* Must handle YouTube transcripts as knowledge source (YouTubeTranscriptApi: https://pypi.org/project/youtube-transcript-api/)
* Must demonstrate clear progression through stages:
   * Base LLM
   * Raw transcript
   * Structured data
   * RAG implementation
   * Interactive features
* Must maintain clear separation between components for teaching purposes
* Must include proper error handling for Japanese text processing
* Must provide clear visualization of RAG process
* Should work within free tier limits where possible

This structure:
1. Sets clear expectations
2. Highlights key technical challenges
3. Defines specific constraints
4. Keeps focus on both learning outcomes and technical implementation

## Knowledgebase

https://github.com/chroma-core/chroma

## Technical Uncertainty

**Q:** How did I address the unavailability of Amazon Nova models in AWS regions near Australia?
**A:** I discovered that Amazon Nova models are not available in the Asia Pacific (Sydney) or Asia Pacific (Melbourne) regions. To overcome this, I selected the US West (Oregon) region as the nearest alternative to manage latency and performance considerations.
Review vid 2: 46:00
https://www.youtube.com/watch?v=A_f0PvCzdJo&list=PL1ZfsqhT9vP4Zxb6MePHeKhBu8OSX8FwK
Video that gets no transcript

Simplified Chinese Scripts
Actual HSK2 example
https://www.youtube.com/watch?v=PO3sdqBbXEo

https://www.youtube.com/watch?v=nWXvJBupwos
https://www.youtube.com/watch?v=KQpXjP0jSsY
https://www.youtube.com/watch?v=_ZZAYcxyAe8

English Subs
https://www.youtube.com/watch?v=xlMBzIwAOlI
https://www.youtube.com/watch?v=SiE6nz7FQt8

No Subs
https://www.youtube.com/watch?v=1WR63ZKmVws&list=PLfj_wyLODBz-TKEfp7N8j5c0pBbKav08B
https://www.youtube.com/watch?v=A_f0PvCzdJo&list=PL1ZfsqhT9vP4Zxb6MePHeKhBu8OSX8FwK


## Bootcamp Week 2: LLA Implementation Report

### Technical Uncertainties

Q: Many HSK2 practice tests on youtube seem not to have chinese subtitles, how to work aroudn this issue.
A: Use YouTube api to implement translation of other subtitles, e.g., English.

1. Language Processing and Localization
Translation Accuracy: Ensuring that all user-facing text, including prompts, messages, and UI elements, is accurately translated into Putonghua. This may require collaboration with language experts to maintain context and meaning.
Handling Bilingual Content: The application currently processes bilingual (Japanese/English) content. Adapting it to handle Putonghua alongside or instead of Japanese will require adjustments in how content is structured and processed.
2. Speech Recognition and Synthesis
ASR (Automatic Speech Recognition): The application may need to integrate or switch to an ASR service that supports Putonghua. This includes evaluating the effectiveness of existing services and potentially finding alternatives that provide accurate transcription for Putonghua.
TTS (Text-to-Speech): Similar to ASR, the application will need to ensure that the TTS service used (e.g., Amazon Polly) supports Putonghua and provides natural-sounding speech.
3. YouTube Transcript Handling
YouTube Transcript API: The current implementation uses the YouTube Transcript API to download transcripts. It is essential to verify whether transcripts are available in Putonghua for the target videos and how to handle cases where transcripts may not exist or are of low quality.
4. Data Storage and Retrieval
SQLite Vector Storage: The application uses SQLite for vector storage. Ensure that the database schema can accommodate Putonghua content and that any text processing (e.g., embeddings) is compatible with the new language.
RAG Implementation: The Retrieval-Augmented Generation (RAG) system must be adapted to retrieve and generate responses based on Putonghua content. This may involve re-evaluating how data is structured and queried.
5. User Interface Adjustments
UI Adaptation: The user interface will need to be adjusted to accommodate Putonghua text, which may have different lengths and formatting compared to Japanese. This includes ensuring that the layout remains user-friendly and visually appealing.
Interactive Features: Any interactive learning features must be tested to ensure they function correctly with Putonghua content, including quizzes and practice scenarios.
6. Error Handling and Debugging
Error Handling for Language Processing: Implement robust error handling for cases where Putonghua text processing fails, ensuring that users receive clear feedback.
Debugging Tools: Ensure that debugging information is relevant for Putonghua, including any metrics or logs that help track the performance of language processing tasks.
7. Technical Restrictions and Compliance
AWS Services: Verify that all AWS services used (e.g., Amazon Bedrock, Transcribe, Polly) support Putonghua and comply with any technical restrictions outlined in the project guidelines.
Free Tier Limits: Ensure that the implementation remains within the free tier limits of the services used, especially when scaling for additional language support.

Summary of Technical Uncertainties
- How to effectively translate and localize the application for Putonghua.
- Availability and quality of ASR and TTS services for Putonghua.
- Handling of YouTube transcripts in Putonghua.
- Adaptation of the database schema and retrieval mechanisms for Putonghua content.
- UI adjustments to accommodate Putonghua text and ensure usability.
- Robust error handling for language processing tasks.




python rag.py
pip install -r requirements.txt



