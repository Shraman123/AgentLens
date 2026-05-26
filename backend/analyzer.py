import json
import os
from typing import List, Dict, Any

from groq import AsyncGroq

# Initialize Groq client
client = AsyncGroq(
    api_key=os.environ.get("GROQ_API_KEY")
)

MODEL = "llama-3.3-70b-versatile"


async def analyze_conversations_batch(
    conversations: List[Dict]
) -> List[Dict]:
    """
    Analyze a batch of conversations to extract:
    - intent
    - sentiment
    - failures
    """

    convs_text = "\n\n".join([
        f"[ID: {c['id']}]\n"
        f"User: {c['user_message']}\n"
        f"Agent: {c['agent_response']}"
        for c in conversations
    ])

    prompt = f"""
You are an AI agent quality analyzer.

Analyze these conversations and extract:

1. intent
- What the user was trying to do
- 2-5 word label
- Examples:
  - "book_flight"
  - "get_refund"
  - "ask_price"

2. sentiment
- "positive"
- "neutral"
- "negative"

3. is_failure
- true if the agent:
  - failed to help
  - gave wrong info
  - refused unnecessarily
  - user seemed frustrated

4. failure_reason
- short explanation if failed
- null otherwise

Respond ONLY with valid JSON array.

Example:
[
  {{
    "id": "abc",
    "intent": "check_order_status",
    "sentiment": "neutral",
    "is_failure": false,
    "failure_reason": null
  }}
]

Conversations:
{convs_text}
"""

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            temperature=0.1,
            max_tokens=4000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        raw = response.choices[0].message.content.strip()

        # Remove markdown formatting if model adds it
        raw = raw.replace("```json", "")
        raw = raw.replace("```", "")
        raw = raw.strip()

        results = json.loads(raw)

        # Ensure every conversation has output
        result_map = {
            r["id"]: r for r in results
        }

        final_results = []

        for c in conversations:
            final_results.append(
                result_map.get(
                    c["id"],
                    {
                        "id": c["id"],
                        "intent": "unknown",
                        "sentiment": "neutral",
                        "is_failure": False,
                        "failure_reason": None
                    }
                )
            )

        return final_results

    except Exception as e:
        print(f"Error analyzing conversations: {e}")

        return [
            {
                "id": c["id"],
                "intent": "unknown",
                "sentiment": "neutral",
                "is_failure": False,
                "failure_reason": None
            }
            for c in conversations
        ]


async def suggest_improved_prompt(
    current_prompt: str,
    failures: List[Dict],
    top_intents: List[Dict]
) -> Dict[str, Any]:
    """
    Suggest an improved system prompt
    based on failures and user intents.
    """

    failures_text = "\n".join([
        (
            f"- User: {f.get('user_message', '')[:100]} "
            f"| Reason: {f.get('failure_reason', 'unknown')}"
        )
        for f in failures[:10]
    ]) or "No failures yet"

    intents_text = ", ".join([
        f"{i['intent']} ({i['cnt']}x)"
        for i in top_intents
    ]) or "None yet"

    prompt = f"""
You are an expert AI prompt engineer.

Based on the failure patterns from a live AI agent,
suggest an improved system prompt.

Current system prompt:
{current_prompt or "(none provided)"}

Top user intents:
{intents_text}

Recent failure patterns:
{failures_text}

Provide a JSON response with:

1. suggested_prompt
- improved system prompt

2. reasoning
- bullet points explaining changes

Respond ONLY with valid JSON.

Example:
{{
  "suggested_prompt": "You are a helpful AI assistant...",
  "reasoning": "- Added clearer refusal handling\\n- Improved factual accuracy instructions"
}}
"""

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            temperature=0.2,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        raw = response.choices[0].message.content.strip()

        # Remove markdown formatting
        raw = raw.replace("```json", "")
        raw = raw.replace("```", "")
        raw = raw.strip()

        result = json.loads(raw)

        return result

    except Exception as e:
        print(f"Error generating prompt suggestion: {e}")

        return {
            "suggested_prompt": current_prompt,
            "reasoning": "Could not generate valid suggestion."
        }