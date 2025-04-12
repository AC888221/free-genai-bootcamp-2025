## ChatGPT Powered Assistant Guide

### Which Model
My free version is ChatGPT-4 Turbo: https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo

### Prompting Guides
ChatGPt-4 Turbo follows standard prompt structuring, without requiring specialized formatting for context retention.

https://www.imaginarycloud.com/blog/chatgpt-prompt-engineering?utm_source=chatgpt.com
> -Be Clear and Specific: Craft detailed prompts to improve response quality. For example, specify preferences like "Give me 5 dog names inspired by popular movies" instead of just asking about dog names.
> -Use Context and Examples: Provide relevant context to guide the model's understanding, leading to more accurate responses. For instance, when asking for gardening advice, add "I'm a beginner with limited space."
> -Set Constraints: Control response length or format by specifying requirements, such as "Provide a 3-sentence summary."
> -Experiment with Question Types: Combine System 1 (quick, instinctive) and System 2 (thoughtful, detailed) questions to diversify response types. For example, ask for a quick list followed by a detailed explanation.
> -Domain-Specific Language: Use relevant terminology for specific fields to ensure more accurate results. For example, include terms like "SEO" or "ROI" when discussing marketing.
> -Control Output Verbosity: Adjust the level of detail by specifying whether you want a concise or thorough response, such as "short and to the point" or "provide detailed steps."
> -Iterate and Improve: Refine your prompts based on previous responses. If the first answer isn’t perfect, tweak the prompt to get better results.
> -Use Open-Ended Prompts for Creativity: For brainstorming or creative tasks, use open-ended prompts that encourage imaginative responses. For example, "Write a short story about a hero who can control the weather."

### Revision of Meta-AI Prompt
The ChatGPT prompt started from the final version of the Meta-AI prompt (#1 p010). In testing the performance of this prompt in ChatGPT vs. Meta, anecdotally, I though that ChatGPT may have a higher temperature setting as its output included phrases in the vocabulary table and more verbose instructions.

ChatGPT was consulted to make revisions to the prompt that aligned with the prompting guide principles:
1. Clarity & Conciseness: Removed redundant phrasing (e.g., "Your goal is to help the student…" → "Your task: Help the student…"); Made the response format explicit using numbered steps (1. Vocabulary table, 2. Sentence pattern, etc.); Used imperative commands for ChatGPT to follow logically.
    - Impact: ChatGPT could follow a structured format more reliably with less preamble.
2. Step-by-Step Structure for Response Generation: improved definition of the response components and itself as a whole (Vocabulary Table, Sentence Pattern Template, Hints, Student Prompt)
    - Impact: ChatGPT could better able to deliver a properly formatted response with less variation.
3. Simplified Example Structure: Switched to a single example showcasing a model response.
    - Impact: ChatGPT could better mimic the structured output format.

This seemed to improve the output by removing potentially conflicting instructions, e.g. be concise yet encouraging, and removing the need for it to interpret scores of good and bad examples.

Further revision was made to align with the the prompting guide principles.

### Observations
- I found the output from ChatGPT to be a bit more stable compared to Meta-AI, for example, consistently producing simplified Chinese Characters.
- Meta-AI seemed to handle the production of the vocabulary table better, producing couplets rather than phrases.
- ChatGPT was able to withhold the answer when asked for it to some extent, while Meta-AI was not. This might be due to the system message (pre-prompt) being set to appease the user. This might also explain why Meta-AI can appear more duplicitous.

## Final Prompt-Output Evaluation:
The final prompt improved the consistency of the output by being more precise, concise, and structured. I think it resulted in a more consistent and tight output.
I reduced the initial support that was offered to the student to encourage more independence but this may have gone too far for beginner language learners.
This prompt is more structured and prescriptive but it seems to yield a better step-by-step task experience, with better balanced gradual support.