import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import json

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

DEPLOYMENT = os.getenv("AZURE_OPENAI_PLANNER_MODEL")


def create_plan(user_query):
    prompt = f"""
You are a planner agent.

Break the user request into clear steps.

Return ONLY valid JSON in this format:
{{
  "steps": [
    {{
      "id": "1",
      "action": "action_name",
      "input": {{}}
    }}
  ]
}}

User request: {user_query}
"""

    response = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    content = response.choices[0].message.content

    # Optional: clean if model adds text
    try:
        return json.loads(content)
    except:
        print("Raw output:", content)
        raise


if __name__ == "__main__":
    query = "Check refund status for order 123 and respond to user"
    plan = create_plan(query)
    print(json.dumps(plan, indent=2))
