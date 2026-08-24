import json
import os
import re
import time
from pydantic import BaseModel, Field, field_validator
from groq import Groq, APIConnectionError, RateLimitError

class TriageDecision(BaseModel):
    category: str = Field(description="Comma-separated business categories: Billing, Technical, Account, Product, Spam, or Out_of_Scope")
    priority: str = Field(description="Strictly one of: P0, P1, P2, P3")
    summary: str = Field(description="1-sentence objective summary in English")
    suggested_action: str = Field(description="Actionable next step for support desk")
    needs_human: bool = Field(description="True if human intervention/review is required")
    confidence: int = Field(description="Confidence score between 0 and 100")

    @field_validator('priority')
    def validate_priority(cls, v):
        v_upper = v.upper().strip()
        if v_upper not in ["P0", "P1", "P2", "P3"]:
            return "P2"
        return v_upper


def get_max_categories(word_count: int) -> int:
    """Enforces dynamic category ceilings to prevent hallucinated category bloat."""
    if word_count <= 4:
        return 1
    elif word_count <= 10:
        return 2
    elif word_count <= 13:
        return 3
    return 5

SYSTEM_PROMPT = """You are an autonomous customer support triage engine.
Analyze the incoming customer message and respond with ONLY a raw JSON object matching this exact structure:
{{
  "category": "Billing, Technical, Account, Product, Spam, or Out_of_Scope",
  "priority": "P0, P1, P2, or P3",
  "summary": "1-sentence summary in English",
  "suggested_action": "Actionable next step",
  "needs_human": true or false,
  "confidence": 0 to 100
}}

RULES:
1. MAX CATEGORIES: You must assign AT MOST {max_cats} categories (comma-separated).
2. SARCASM & SENTIMENT: Watch for sarcasm (inverted polarity). If a user uses sarcastic praise for a failure (e.g., 'Great job breaking my app'), identify it as High Frustration and assign P0.
3. PRIORITY MATRIX:
   - P0: System-wide downtime, checkout/payment 500 API errors, legal/regulatory threats, active data loss, furious churn risk.
   - P1: Account lockout, standard billing/payment disputes, major functional breakage.
   - P2: Minor bugs, confusing UX, general inquiries requiring human action.
   - P3: Simple FAQs, feature requests, spam, auto-handled items.
4. NEEDS_HUMAN:
   - Set to true for: legal/chargeback threats, account lockouts or broken authentication (e.g., password reset failure), multi-issue confusion, low confidence, non-English messages requiring native review.
   - Set to false for: simple informational queries, standard feature requests, obvious spam.
5. TRANSLATION: If the message is non-English, summarize and provide the suggested action in English.
6. GROUNDING: Do NOT invent facts, order numbers, or names not present in the text.
7. OUTPUT FORMAT: Respond ONLY with the JSON object. Do not output markdown code fences, backticks, or preamble.
8. TOOL CITATION: If TOOL CONTEXT is provided, you MUST explicitly reference it in your suggested_action (e.g., start with "Per DB lookup..." or "Runbook indicates...")."""

class CoreEngine:
    def __init__(self, model_name: str = "openai/gpt-oss-120b"):
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model_name = model_name
    
    def triage(self, cleaned_text: str, original_raw_text: str, tool_context: str = "") -> dict:
        word_count = len(original_raw_text.split())
        max_cats = get_max_categories(word_count)
        formatted_prompt = SYSTEM_PROMPT.format(max_cats=max_cats)
        
        # Add a rule to the system prompt about tools
        if tool_context:
            formatted_prompt += "\n8. TOOL CONTEXT: You have been provided internal DB/RAG data. Use it to inform your summary and suggested action."

        # Retry loop for resilience against transient network drops
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    temperature=0.0,
                    messages=[
                        {"role": "system", "content": formatted_prompt},
                        {"role": "user", "content": f"<<<RAW_MESSAGE>>>\n{cleaned_text}\n<<<END_MESSAGE>>>{tool_context}\nRespond strictly with the raw JSON object."}
                    ]
                )
                raw_content = response.choices[0].message.content.strip()
                
                # Defensive JSON extraction
                json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
                raw_json_str = json_match.group(0) if json_match else raw_content
                raw_json = json.loads(raw_json_str)

                validated = TriageDecision(**raw_json)
                return validated.model_dump()

            except (APIConnectionError, RateLimitError, Exception) as e:
                if attempt < max_retries - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                return {
                    "category": "Technical",
                    "priority": "P1",
                    "summary": "Network connectivity error during autonomous triage.",
                    "suggested_action": "Manual review required due to upstream connection timeout.",
                    "needs_human": True,
                    "confidence": 0
                }