from planner import create_plan
from executor import execute_plan

query = "Check refund status for order 123 and respond to user"

plan = create_plan(query)
print("\nGenerated Plan:\n", plan)

result = execute_plan(plan)

print("\nFinal Output:")
print(result.get("final_response"))
