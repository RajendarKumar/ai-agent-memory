from datetime import date
from pathlib import Path
from typing import Any, Callable, Literal
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from refund_agent.domain.models import RefundState
from refund_agent.infrastructure.llm import RefundLanguageModel
from refund_agent.infrastructure.orders import find_order_by_id, load_orders
from refund_agent.memory.long_term import MilvusMemory
from refund_agent.memory.session import SessionMemory
from refund_agent.memory.short_term import ShortTermMemory


class RefundWorkflow:
    def __init__(
        self,
        language_model: RefundLanguageModel,
        orders_file: Path,
        session_memory: SessionMemory,
        long_term_memory: MilvusMemory | None = None,
        approval_handler: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.language_model = language_model
        self.orders_file = orders_file
        self.session_memory = session_memory
        self.long_term_memory = long_term_memory
        self.approval_handler = approval_handler or self._print_approval
        self.graph = self._build_graph()

    def run(
        self,
        email_body: str,
        refund_policy: str,
        thread_id: str,
        evaluation_date: date | None = None,
    ) -> RefundState:
        request = ShortTermMemory(
            email_body=email_body,
            refund_policy=refund_policy,
            evaluation_date=evaluation_date or date.today(),
        )
        return self.graph.invoke(
            request.as_state(),
            config={"configurable": {"thread_id": thread_id}},
        )

    def _build_graph(self):
        def extract(state: RefundState) -> dict:
            details = self.language_model.extract_email_details(state["email_body"])
            query = f"{details.category} refund policy {state['refund_policy']}"
            memories = self.long_term_memory.search(query) if self.long_term_memory else []
            return {"extracted": details.model_dump(mode="json"), "related_memories": memories}

        def lookup(state: RefundState) -> dict:
            orders = load_orders(self.orders_file)
            order = find_order_by_id(orders, state["extracted"].get("order_number"))
            return {"order": order}

        def evaluate_policy(state: RefundState) -> dict:
            result = self.language_model.evaluate_refund(
                order=state["order"] or {},
                refund_policy=state["refund_policy"],
                evaluation_date=state["evaluation_date"],
                related_memories=state.get("related_memories", []),
            )
            return {"policy_result": result.model_dump()}

        def send_for_approval(state: RefundState) -> dict:
            self.approval_handler(
                {"order": state["order"], "policy_result": state["policy_result"]}
            )
            return {"status": "PENDING_HUMAN_APPROVAL"}

        def reject(state: RefundState) -> dict:
            if state.get("order") is None:
                return {"status": "REJECTED", "reason": "Order not found"}
            return {
                "status": "REJECTED",
                "reason": state.get("policy_result", {}).get("reason", "Refund not approved"),
            }

        def remember_outcome(state: RefundState) -> dict:
            if self.long_term_memory and state.get("policy_result"):
                category = state.get("extracted", {}).get("category", "other")
                decision = state["policy_result"].get("refund_possible", "NOT SURE")
                self.long_term_memory.add(
                    f"Historical refund case: category {category}; policy decision {decision}.",
                    metadata={"category": category, "decision": decision, "id": str(uuid4())},
                )
            return {}

        def route_after_lookup(state: RefundState) -> Literal["evaluate_policy", "reject"]:
            return "reject" if state.get("order") is None else "evaluate_policy"

        def route_after_policy(state: RefundState) -> Literal["send_for_approval", "reject"]:
            return "reject" if state["policy_result"]["refund_possible"] == "NO" else "send_for_approval"

        builder = StateGraph(RefundState)
        builder.add_node("extract", extract)
        builder.add_node("lookup", lookup)
        builder.add_node("evaluate_policy", evaluate_policy)
        builder.add_node("send_for_approval", send_for_approval)
        builder.add_node("reject", reject)
        builder.add_node("remember_outcome", remember_outcome)
        builder.add_edge(START, "extract")
        builder.add_edge("extract", "lookup")
        builder.add_conditional_edges("lookup", route_after_lookup)
        builder.add_conditional_edges("evaluate_policy", route_after_policy)
        builder.add_edge("send_for_approval", "remember_outcome")
        builder.add_edge("reject", "remember_outcome")
        builder.add_edge("remember_outcome", END)
        return builder.compile(checkpointer=self.session_memory.checkpointer)

    @staticmethod
    def _print_approval(data: dict[str, Any]) -> None:
        print("\n--- Refund request pending human approval ---")
        print(data)