# Multi-Agent Customer Support

## Overview

This repository implements a small multi-agent customer support system using Azure OpenAI and Azure Cosmos DB. The design is built around a planner-executor-critic pattern:

- `planner.py`: converts a user request into a structured plan.
- `executor.py`: executes the plan by invoking domain-specific tools.
- `critic.py`: evaluates the final output against the original user request.
- `state.py`: persists session state in Azure Cosmos DB.

The system is architected as a pipeline of specialized agents, with a clear separation between orchestration, tool execution, and evaluation.

## System Goals

- Support clear decomposition of user requests into actions.
- Maintain persistent session state for reliability and observability.
- Provide a mechanism to verify and retry outputs when they are insufficient.
- Keep tool integration extensible through a registry.
- Use Azure Foundry / Azure OpenAI for language planning and critique.

## Architecture

### High-level flow

1. Client request arrives in `main.py`.
2. `planner.py` generates a plan using the planner LLM.
3. `executor.py` runs each plan step against a tool registry.
4. Execution results are stored in the session state.
5. `critic.py` scores the final response.
6. If quality is insufficient, the system can retry.

### Core components

- `main.py`: orchestration and retry control.
- `planner.py`: plan creation and JSON schema enforcement.
- `executor.py`: executes actions using resolver logic and tool dispatch.
- `critic.py`: validation and scoring of results.
- `state.py`: session persistence using Cosmos DB.
- `tools/registry.py`: central tool mapping and discovery.
- `tools/refund_tools.py`: sample domain tools for order/refund data.
- `tools/response_tools.py`: response generation tool.

## Detailed Design

### Planner Agent

`planner.py` is responsible for converting natural language into a machine-consumable plan.

Responsibilities:

- Build a prompt template for the planner model.
- Call Azure OpenAI chat completions.
- Parse model output as JSON.
- Enforce the plan schema:
  - `steps` array
  - each step has `id`, `action`, and `input`

Example plan:

```json
{
  "steps": [
    {
      "id": "1",
      "action": "get_order_details",
      "input": {
        "order_id": "123"
      }
    },
    {
      "id": "2",
      "action": "check_refund_status",
      "input": {
        "order_id": "123"
      }
    },
    {
      "id": "3",
      "action": "generate_response",
      "input": {
        "order_id": "123",
        "refund_status": "{{step.2.refund_status}}"
      }
    }
  ]
}
```

Key assumptions:

- The planner model will return JSON only.
- The model understands a small, fixed action set.
- Plan outputs are deterministic with `temperature=0`.

### Executor Agent

`executor.py` converts plan steps into actual tool calls.

Responsibilities:

- Load available tools from `tools/registry.py`.
- Map planner actions to tool functions using `ACTION_MAP`.
- Resolve dynamic inputs using a simple placeholder syntax.
- Execute tools in order and aggregate context.

Low-level behavior:

- `resolve_inputs(inputs, context)` scans strings for `{{step.<step_id>.<field>}}` patterns.
- A step action is mapped to a tool key.
- Tools are invoked with either explicit step inputs or the current context.
- If a tool returns a dict, the context is updated with its keys.
- If a tool returns a primitive/string, it is stored as `final_response`.

Example execution path:

- Step 1: `get_order_details(order_id=123)` returns order metadata.
- Step 2: `check_refund_status(order_id=123)` returns refund state.
- Step 3: `generate_response(order_id=123, refund_status='processing')` returns the final sentence.

### Critic Agent

`critic.py` is used to verify whether the final response satisfies the original query.

Responsibilities:

- Prompt the critic model with the user query and output.
- Request a normalized JSON response with:
  - `score` between 0 and 1
  - `feedback` text
- Parse and return the score for decision-making.

Design note:

- The critic uses the same `DEPLOYMENT` model from environment variables, but this can be split into a dedicated critic deployment for production.

### State Persistence

`state.py` manages session persistence in Azure Cosmos DB.

Session model:

```json
{
  "id": "<uuid>",
  "session_id": "<uuid>",
  "status": "created|planning_done|execution_done|completed",
  "history": [],
  "plan": { ... },
  "execution_result": { ... },
  "critic": { "score": 0.8, "feedback": "..." },
  "final_response": "..."
}
```

Design responsibilities:

- `create_session()` creates a new Cosmos DB item.
- `update_session(session_id, data)` reads the existing item, updates fields, and upserts.
- `get_session(session_id)` returns the persisted session state.

### Tool Registry and Domain Tools

`tools/registry.py` exposes a single mapping from logical tool names to implementation functions.

Benefits:

- Easy extensibility for new actions.
- Single place to manage tool discovery.
- Clear separation between planner action names and tool implementations.

Example tool definitions:

- `refund_tools.get_order_details(order_id)`
- `refund_tools.check_refund_status(order_id)`
- `response_tools.generate_response(order_id=None, refund_status=None)`

These are stubs for a real domain service layer.

## Low-Level Design (LLD)

### Modules and Interfaces

- `main.py`
  - `session_id = create_session()`
  - loop retries up to `MAX_RETRIES`
  - `plan = create_plan(query)`
  - `result = execute_plan(plan)`
  - `evaluation = evaluate_response(query, final_response)`
  - conditional retry and session updates

- `planner.py`
  - `create_plan(user_query) -> dict`

- `executor.py`
  - `resolve_inputs(inputs: dict, context: dict) -> dict`
  - `execute_plan(plan: dict) -> dict`

- `critic.py`
  - `evaluate_response(user_query: str, result: str) -> dict`

- `state.py`
  - `create_session() -> str`
  - `update_session(session_id: str, data: dict) -> None`
  - `get_session(session_id: str) -> dict`

- `tools/registry.py`
  - `load_tools() -> dict`

- `tools/refund_tools.py`
  - `get_order_details(order_id: str) -> dict`
  - `check_refund_status(order_id: str) -> dict`

- `tools/response_tools.py`
  - `generate_response(order_id=None, refund_status=None, **kwargs) -> str`

### Data Flow and State

- Input: raw user query
- Output: final textual answer
- Intermediate artifacts:
  - planner JSON plan
  - decision context object filled during execution
  - persisted session document in Cosmos DB

The session document is the source of truth for auditability and retries.

### Error Handling and Retry Strategy

Current behavior in `main.py`:

- Each run creates a new session.
- The system retries up to `MAX_RETRIES` if critic score is not good enough.
- A failed critic causes the loop to continue.

Design considerations:

- The retry loop is simple but effective for transient LLM mistakes.
- In production, a more advanced retry policy would add backoff and error classification.
- The session store allows retries to resume from a previously recorded plan or result.

## System Design Interview Perspective

### What problem does this solve?

This system turns unstructured support requests into deterministic tool-driven workflows, then verifies correctness with a critic agent. It is designed for customer support scenarios like refund status, order status, and agent-assisted responses.

### Component boundaries

- Planner: language understanding and workflow decomposition.
- Executor: deterministic tool orchestration.
- Critic: outcome validation.
- Persistence: state and session tracking.
- Tools: domain knowledge and data access.

This clean separation supports maintainability, testing, and independent scaling.

### Scaling and Operations

- Stateless orchestration (`main.py`, `planner.py`, `executor.py`, `critic.py`) can scale horizontally.
- Cosmos DB stores immutable session records and user-visible history.
- Tool implementations can be replaced by networked microservices or API clients.
- The planner and critic models are external dependencies; use Azure OpenAI deployments with proper rate limiting.

### Key tradeoffs

- Simplicity vs flexibility: the current design is small and direct, but depends on a fixed `ACTION_MAP` and explicit placeholders.
- Oracle dependency: `critic.py` uses the same LLM as the planner, which means evaluation may inherit the same failures.
- Strong assumption: planner returns valid JSON. Production should add robust JSON extraction and schema validation.

### Bottlenecks and risks

- LLM hallucination in both planning and critique.
- Tool input resolution uses simple regex replacement; complex nested references are unsupported.
- Cosmos DB read/update per step may become expensive if the system evolves to update state after every action.

## Deployment and Configuration

### Required environment variables

- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_VERSION`
- `AZURE_OPENAI_PLANNER_MODEL`
- `COSMOS_ENDPOINT`
- `COSMOS_KEY`

### Running locally

1. Create a `.env` file with the Azure and Cosmos values.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the orchestrator:

```bash
python main.py
```

## Future Improvements

- Add strong JSON schema validation using `pydantic` or `jsonschema`.
- Replace static `ACTION_MAP` with self-describing tool metadata.
- Add a dedicated critic model and a separate deployment for evaluation.
- Support asynchronous execution for slow external tools.
- Add a request parser to derive entity values like `order_id` automatically.
- Expand session history with timestamped action logs.
- Add unit tests for planner, executor, and tools.

## Summary

This project demonstrates a modular multi-agent architecture using Azure AI and Cosmos DB. The design emphasizes:

- clear agent roles,
- persistent session tracking,
- extensible tool integration,
- and iterative quality assurance via a critic loop.

It is a strong foundation for building a production-ready, agent-driven customer support workflow in Azure Foundry.
