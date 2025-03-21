Key Issues in Your Testing Code
Looking at your test code and the GPT-SoVITS API documentation:

Your test_endpoints functions aren't specifically testing the GPT-SoVITS endpoints correctly
The GPT-SoVITS API requires specific parameters that may be missing in your requests
Your test configuration doesn't match the expected format for the GPT-SoVITS API

GPT-SoVITS Endpoints
From the first document, here are the main endpoints:

/tts - For text-to-speech conversion
/control - For service control (restart/exit)
/set_gpt_weights - To change GPT model weights
/set_sovits_weights - To change SoVITS model weights

Common Issues and Required Parameters
Based on the GPT-SoVITS code, here are the mandatory parameters for the TTS endpoint:

text - Text to be synthesized (required)
text_lang - Language of the text (required, must be in supported languages)
ref_audio_path - Reference audio path (required)
prompt_lang - Language of the prompt text (required, must be in supported languages)
text_split_method - Text split method (must be in supported methods, default is "cut5")

Make sure that:

The audio file referenced by ref_audio_path actually exists in the system
The languages specified are supported by your GPT-SoVITS installation
For GET requests, all parameters are properly URL-encoded


Overview
This document aims to introduce how to use our Text-to-Speech API, including making requests via GET and POST methods. This API supports converting text into the voice of specified characters and supports different languages and emotional expressions.

Character and Emotion List
To obtain the supported characters and their corresponding emotions, please visit the following URL:

URL: http://127.0.0.1:5000/character_list
Returns: A JSON format list of characters and corresponding emotions
Method: GET
{
    "Hanabi": [
        "default",
        "Normal",
        "Yandere",
    ],
    "Hutao": [
        "default"
    ]
}
Regarding Aliases
From version 2.2.4, an alias system was added. Detailed allowed aliases can be found in Inference/params_config.json.

Text-to-Speech
URL: http://127.0.0.1:5000/tts
Returns: Audio on success. Error message on failure.
Method: GET/POST
GET Method
Format
http://127.0.0.1:5000/tts?character={{characterName}}&text={{text}}
Parameter explanation:
character: The name of the character folder, pay attention to case sensitivity, full/half width, and language (Chinese/English).
text: The text to be converted, URL encoding is recommended.
Optional parameters include text_language, format, top_k, top_p, batch_size, speed, temperature, emotion, save_temp, and stream, detailed explanations are provided in the POST section below.
From version 2.2.4, an alias system was added, with detailed allowed aliases found in Inference/params_config.json.
POST Method
JSON Package Format
All Parameters
{
    "method": "POST",
    "body": {
        "character": "${chaName}",
        "emotion": "${Emotion}",
        "text": "${speakText}",
        "text_language": "${textLanguage}",
        "batch_size": ${batch_size},
        "speed": ${speed},
        "top_k": ${topK},
        "top_p": ${topP},
        "temperature": ${temperature},
        "stream": "${stream}",
        "format": "${Format}",
        "save_temp": "${saveTemp}"
    }
}
You can omit one or more items. From version 2.2.4, an alias system was introduced, detailed allowed aliases can be found in Inference/params_config.json.

Minimal Data:
{
    "method": "POST",
    "body": {
        "text": "${speakText}"
    }
}
Parameter Explanation
text: The text to be converted, URL encoding is recommended.

character: Character folder name, pay attention to case sensitivity, full/half width, and language.

emotion: Character emotion, must be an actually supported emotion of the character, otherwise, the default emotion will be used.

text_language: Text language (auto / zh / en / ja), default is multilingual mixed.

top_k, top_p, temperature: GPT model parameters, no need to modify if unfamiliar.

batch_size: How many batches at a time, can be increased for faster processing if you have a powerful computer, integer, default is 1.

speed: Speech speed, default is 1.0.

save_temp: Whether to save temporary files, when true, the backend will save the generated audio, and subsequent identical requests will directly return that data, default is false.

stream: Whether to stream, when true, audio will be returned sentence by sentence, default is false.

format: Format, default is WAV, allows MP3/ WAV/ OGG.