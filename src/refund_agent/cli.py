import argparse
from datetime import date
from pathlib import Path

from refund_agent.application.workflow import RefundWorkflow
from refund_agent.infrastructure.config import Settings
from refund_agent.infrastructure.llm import RefundLanguageModel
from refund_agent.memory.long_term import MilvusMemory
from refund_agent.memory.session import SessionMemory


def main() -> None:
	parser = argparse.ArgumentParser(description="Evaluate a refund request received by email.")
	parser.add_argument("--email", required=True, help="Email body to evaluate")
	parser.add_argument("--policy", required=True, help="Current refund policy text")
	parser.add_argument("--thread-id", default="refund-cli", help="Conversation ID for session memory")
	parser.add_argument("--evaluation-date", type=date.fromisoformat)
	parser.add_argument("--orders", type=Path, help="Override ORDERS_FILE")
	args = parser.parse_args()

	settings = Settings.from_env()
	language_model = RefundLanguageModel(settings.groq_api_key, settings.groq_model)
	long_term_memory = None
	if settings.long_term_memory_enabled:
		long_term_memory = MilvusMemory(
			uri=settings.milvus_uri,
			token=settings.milvus_token,
			collection=settings.milvus_collection,
		)

	try:
		with SessionMemory(settings.session_db) as session_memory:
			workflow = RefundWorkflow(
				language_model=language_model,
				orders_file=args.orders or settings.orders_file,
				session_memory=session_memory,
				long_term_memory=long_term_memory,
			)
			result = workflow.run(
				email_body=args.email,
				refund_policy=args.policy,
				thread_id=args.thread_id,
				evaluation_date=args.evaluation_date,
			)
			print(f"Status: {result['status']}")
			if result.get("reason"):
				print(f"Reason: {result['reason']}")
	finally:
		if long_term_memory:
			long_term_memory.close()
