from typing import List
import logging

logger = logging.getLogger(__name__)

def get_hsk_prompt(hsk_level: str) -> str:
    """Get the appropriate system prompt for the selected HSK level."""
    hsk_prompts = {
        "HSK 1 (Beginner)": """Language Rules:
1. Only use HSK 1 vocabulary (150 basic words)
2. Use simple greetings: 你好, 再见
3. Basic pronouns: 我, 你, 他
4. Simple verbs: 是, 有, 喜欢
5. Keep sentences under 5 words
Example: 你好！我是老师。""",
        
        "HSK 2 (Basic)": """Language Rules:
1. Use HSK 1-2 vocabulary (300 words)
2. Simple time expressions: 今天, 明天
3. Basic questions: 什么, 谁, 哪里
4. Common actions: 吃, 喝, 说, 看
5. Keep sentences under 8 words
Example: 今天天气很好，我很高兴。""",
        
        "HSK 3 (Elementary)": """Language Rules:
1. Use HSK 1-3 vocabulary (600 words)
2. Express opinions: 我觉得, 我认为
3. Time and sequence: 以前, 然后, 最后
4. Compare things: 比, 更, 最
5. Keep sentences under 10 words
Example: 我觉得学习中文很有意思。""",
        
        "HSK 4 (Intermediate)": """Language Rules:
1. Use HSK 1-4 vocabulary (1200 words)
2. Complex emotions: 激动, 失望, 担心
3. Abstract concepts: 经验, 机会, 建议
4. Use 因为...所以... structures
5. Keep sentences under 15 words
Example: 因为你说得很好，所以我很佩服你。""",
        
        "HSK 5 (Upper-Intermediate)": """Language Rules:
1. Use HSK 1-5 vocabulary (2500 words)
2. Professional terms: 研究, 调查, 分析
3. Complex opinions: 据我所知, 在我看来
4. Use idioms carefully: 马马虎虎, 半途而废
5. Keep sentences under 20 words
Example: 在我看来，学习语言需要持之以恒。""",
        
        "HSK 6 (Advanced)": """Language Rules:
1. Use full HSK vocabulary (5000+ words)
2. Academic language: 理论, 观点, 假设
3. Literary expressions: 引经据典
4. Complex structures: 不但...而且..., 即使...也...
5. Keep sentences under 25 words
Example: 掌握一门语言不仅需要勤奋，而且要有正确的学习方法。"""
    }
    return hsk_prompts.get(hsk_level, hsk_prompts["HSK 1 (Beginner)"])

# Topic Prompts
TOPICS = [
    "General Conversation",
    "Travel & Transportation",
    "Food & Dining",
    "Business & Work",
    "Technology & Internet",
    "Education & Study",
    "Health & Wellness",
    "Culture & Entertainment",
    "Shopping & Services",
    "Family & Relationships"
]

def get_topic_prompt(selected_topics: List[str]) -> str:
    """Generate prompt based on selected topics."""
    if "General Conversation" in selected_topics or not selected_topics:
        return "Feel free to discuss any appropriate topic while maintaining the language level requirements."
    
    topics_str = ", ".join(selected_topics)
    return f"""Please focus the conversation on these topics: {topics_str}.
Try to relate responses to these areas when appropriate while maintaining the language level requirements.
If the user's question is unrelated to these topics, gently guide the conversation back to the selected topics."""

# Formality Level Prompts
FORMALITY_LEVELS = {
    "Casual": """Use casual, friendly language as if speaking with friends:
- Use informal pronouns and expressions
- Include common colloquialisms appropriate for the HSK level
- Feel free to use friendly particles like 啊, 呢, 吧
- Keep the tone light and conversational""",

    "Neutral": """Use standard, everyday Putonghua suitable for most situations:
- Balance between formal and informal language
- Use standard grammatical structures
- Maintain a friendly but respectful tone
- Suitable for general daily conversations""",

    "Formal": """Use polite, formal language appropriate for professional settings:
- Use respectful pronouns and titles
- Choose more formal vocabulary variants
- Maintain professional distance
- Avoid colloquialisms""",

    "Highly Formal": """Use highly formal language suitable for academic or official occasions:
- Use the most formal honorifics and titles
- Employ sophisticated vocabulary (within HSK level)
- Use complex grammatical structures (within HSK level)
- Maintain a scholarly or official tone"""
}

def get_formality_prompt(formality_level: str) -> str:
    """Get the formality-specific prompt."""
    if formality_level not in FORMALITY_LEVELS:
        logger.warning(f"Unknown formality level: '{formality_level}'. Available levels: {list(FORMALITY_LEVELS.keys())}")
        return FORMALITY_LEVELS["Neutral"]
    
    return FORMALITY_LEVELS[formality_level]

def get_goal_prompt(goal: str) -> str:
    """Generate prompt based on user's learning goal."""
    if not goal.strip():
        return ""
    
    return f"""Specific Learning Goal:
- Help the user practice and achieve this goal: {goal}
- Provide gentle corrections and guidance related to this goal
- Create opportunities to practice this specific aspect
- Give encouragement when the user makes progress towards this goal"""

def get_summary_prompt(conversation_text: str) -> str:
    """Generate a prompt for conversation summarization."""
    return f"""Please provide a concise summary of this conversation that will be used for maintaining context in future responses.

The conversation contains two parts:
1. Previous Summary: Earlier parts of the conversation that were already summarized
2. New Messages: Recent messages that need to be incorporated into a new summary

When creating the summary:
- Focus on information that remains relevant for the ongoing conversation
- Give more weight to recent messages as they represent the current direction of the conversation
- Include key topics, decisions, or preferences mentioned
- Keep the summary concise but informative

Conversation to summarize:

{conversation_text}

Summary:""" 