from typing import TypedDict, Literal

#Define the structure for email classification
class EmailClassification(TypedDict):
    intent: Literal["question", "bug", "billing", "feature", "complex"]
    urgency: Literal["low", "medium", "high", "critical"]
    topic: str
    summary: str

class EmailAgentState(TypedDict):
    email_content: str
    sender_email: str
    email_id: str

# classification result
classification: EmailClassification | None

# Raw search/API results
search_results: list[str] | None
customer_history: dict | None

# Generated content
draft_response: str | None
messages: list[str] | None


# Handling different type of errors

# TRANSIENT ERRORS
# from langgraph.types import RetryPolicy
# workflow.add_node(
#     "search_documentation",
#     search_documentation,
#     retry_policy=RetryPolicy(max_attempts=3, initial_interval=1.0)
# )

# LLM RECOVERABLE
# from langgraph.types import Command
# def execute_tool(state: State) -> Command[Literal["agent", "execute_tool"]]:
#     try:
#         result = run_tool(state['tool_call'])
#         return Command(update={"tool_result": result}, goto="agent")
#     except ToolError as e:
#         # Let the LLM see what went wrong and try again
#         return Command(
#             update={"tool_result": f"Tool error: {str(e)}"},
#             goto="agent"
#         )


# USER FIXABLE
# from langgraph.types import Command
# def lookup_customer_history(state: State) -> Command[Literal["draft_response"]]:
#     if not state.get('customer_id'):
#         user_input = interrupt({
#             "message": "Customer ID needed",
#             "request": "Please provide the customer's account ID to look up their subscription history"
#         })
#         return Command(
#             update={"customer_id": user_input['customer_id']},
#             goto="lookup_customer_history"
#         )
#     #Now proceed with lookup
#     customer_data = fetch_customer_history(state['customer_id'])
#     return Command(update={"customer_history": customer_data}, goto="draft_response")

# # UNEXPECTED
# def send_reply(state: EmailAgentState):
#     try:
#         email_service.send(state["draft_response"])
#     except Exception:
#         raise #Surface unexpected errors
