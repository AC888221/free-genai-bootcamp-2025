## Hypothesis and Technical Uncertainty
I evaluated two free AI-powered assistants, Meta AI and ChatGPT. My initial hypothesis was that free AI-powered assistance would struggle to perform the expected task.
Additionally, I was uncertain how to optimize prompts to achieve the best outcome from these free AI tools. Since cost is a key consideration for me, I also aimed to compare their performance to determine which free assistant performed better.

## Technical Exploration
I built a prompt document incrementally, first with Meta Al (Llama 3 70B), then with Chat GPT4 Turbo (Free). I evaluated the prompts across assistants when I switched and when I finished.

#### Meta AI Exploration
During my exploration of Meta AI, I encountered several challenges and inconsistencies. The model claimed to be running different versions of Llama (2, 3, 3.1, and 3.2) at different times, raising concerns about reliability. Additionally, initial testing revealed that Meta AI could not properly render Simplified Chinese characters, which it acknowledged as a system limitation. However, the next day, it successfully displayed Chinese characters and claimed a backend update had resolved the issue. This contradiction in self-reporting made it difficult to fully trust its responses.

To optimize my prompt, I defined the AI assistants role e.g. (teacher), objective (e.g. help student construct sentence), persona (e.g., encouraging), expected output (e.g. vocab table), and limitations (e.g. withhold answer).
In the end, I was pleasantly surprised at how well Meta AI did. It was able to produce a useful output that could be useful to a motivated and diligent student. However, it was a bit frustrating how inconsistent the output could be across different sessions (e.g. different days), suggesting some internal parameters were changing in between (perhaps greater usage history routed the queries to better model versions).

#### ChatGPT Exploration
I used the final Meta AI prompt template as a base when exploring ChatGPT and in my initial testing I found the output to be more variable than I experienced with Meta AI, leading me to think it might have a higher temperature setting. However, on reviewing the prompt, I concluded that the model was interpreting the prompt in unexpected ways, in particular the scored example, which was very interpretation based. So, following advice from a prompt guide I made the prompt more precise, concise, and explicit, removing potential conflict from system interpretation.

In the end, I was very pleased with the outcome. The output followed the prompt instructions well and ChatGPT was able to follow initial instructions across interactions. It still gave up the answer too early when pressed but I think there is still room to further improve it with more time. It gives me hope that a free/low-cost option for the system is possible.

## Final Outcomes
- Model Reliability: Meta AI’s shifting claims about its capabilities and inconsistent performance made it less trustworthy compared to ChatGPT, which demonstrated greater stability.  Meta AI also displayed poor reliability in its rendering of simplified Chinese characters, not being able to do it when I first explored it, then being able to, and finally going back to being unable to render them when I tested the final ChatGPT prompt on it.
- Clearly Defined and Structured Prompt: Clearly defining what the AI should do significantly improves response quality. Cluttered and overly complex prompts can cause AI assistants to misinterpret the user’s intent.
- Free-tier Performance: ChatGPT emerged as the better free-tier AI assistant for Putonghua learning, offering better reliability and confidence.

## Possible Further Steps
- Refine Feedback in Subsequent Prompts: Add back the feedback from the Meta AI prompt and expand upon it, making it more personal and iterative,
- Further Investigate Multi-turn Memory: Investigate how well the AI performs in different aspects of retaining context across multiple interactions.
- Further test COSTAR Framework: I read about the COSTAR framework and tried to fit my prompt into the framework but it seemed more focused on the persona of the AI and I was concerned that it was making my prompt more confusing. However, given more time this could be worth exploring.
- Test Different Language Levels: See whether intermediate and advanced level versions work as well.
