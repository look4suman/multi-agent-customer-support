from planner import create_plan
from executor import execute_plan
from critic import evaluate_response
from state import create_session, update_session

query = "Check refund status for order 123 and respond to user"

session_id = create_session()

MAX_RETRIES = 2

for attempt in range(MAX_RETRIES):
    print(f"\n--- Attempt {attempt + 1} ---")

    plan = create_plan(query)

    update_session(session_id, {
        "plan": plan,
        "status": "planning_done"
    })

    result = execute_plan(plan)

    update_session(session_id, {
        "execution_result": result,
        "status": "execution_done"
    })

    final_response = result.get("final_response")

    evaluation = evaluate_response(query, final_response)

    update_session(session_id, {
        "critic": evaluation
    })

    if evaluation["score"] > 0.8:
        update_session(session_id, {
            "final_response": final_response,
            "status": "completed"
        })

        print("\n✅ Final Answer:", final_response)
        break
    else:
        print("\n⚠️ Retrying...")

else:
    print("\n❌ Failed")
