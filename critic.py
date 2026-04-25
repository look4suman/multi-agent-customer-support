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


def evaluate_response(user_query, result):
    prompt = f"""
    You are a critic agent.

    Evaluate if the response correctly answers the user query.

    Return ONLY JSON:
    {{
    "score": number (0 to 1),
    "feedback": "what is wrong if any"
    }}

    User query: {user_query}

    System output:
    {result}
    """

    response = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except:
        print("Critic raw output:", content)
        raise
