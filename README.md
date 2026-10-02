# Refund Agent

An email-based refund evaluation application. It extracts request details with
Groq, looks up the order in CSV or JSON, evaluates the supplied refund policy,
and routes eligible cases for human approval. LangGraph manages the workflow;
SQLite stores conversation checkpoints; Milvus provides optional long-term
vector retrieval.

For a complete execution walkthrough, Java-to-Python explanations, and
class-by-class coverage of LangGraph, SQLite, Groq, and Milvus, see the
[Refund Flow Guide](docs/REFUND_FLOW_GUIDE.md).

## Requirements

- macOS or Linux
- Python 3.11 or newer (the project environment was verified with Python 3.12)
- A Groq API key
- Docker Milvus reachable at `http://localhost:19530` when long-term memory is
   enabled

## Step 1: Open the Project

In Terminal, change to the directory containing this README:

```sh
cd /path/to/ai_agent_rag
```

Replace the path with the actual project location.

## Step 2: Create and Activate the Environment

Use a Python 3.11+ executable. On macOS, if `python3.12` is installed:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python --version
```

The version printed must be 3.11 or newer. If `.venv` already exists, skip the
creation command and activate it. If `python3.12` is unavailable, substitute
the command for an installed Python 3.11+ interpreter.

## Step 3: Install the Project

With `.venv` activated, run:

```sh
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`requirements.txt` installs the project in editable mode and includes the
runtime and test dependencies declared in `pyproject.toml`.

## Step 4: Configure Environment Variables

Create `.env` from the template only if it does not already exist:

```sh
test -f .env || cp .env.example .env
```

Open `.env` in your editor and set `GROQ_API_KEY` to your Groq key. The current
defaults use the synthetic `data/orders.csv`, SQLite at `data/refund_sessions.sqlite3`,
Milvus at `http://localhost:19530`, and the `refund_memories` collection.
`MILVUS_TOKEN` may stay blank for the current local Milvus instance, which
accepts unauthenticated requests.

Do not paste `.env` contents into chat or commit this file. Use synthetic data
for initial tests. LangSmith tracing sends workflow inputs and outputs to
LangSmith; set `LANGSMITH_TRACING=false` in `.env` unless you intentionally want
that tracing.

## Step 5: Check Milvus

The local Docker instance should be running before you start the application:

```sh
docker ps --filter name=milvus-standalone
```

The container should show as running and publish port `19530`. You can verify
the HTTP API with:

```sh
curl -sS -X POST http://localhost:19530/v2/vectordb/collections/list \
   -H 'Content-Type: application/json' \
   -d '{"dbName":"default"}'
```

When `LONG_TERM_MEMORY_ENABLED=true`, the app creates `refund_memories` if it
does not already exist. FastEmbed downloads its embedding model on the first
initialization, so the first run may take longer and requires network access.

## Step 6: Run a Refund Request

The complete synthetic request in [examples/refund_request.txt](examples/refund_request.txt)
uses order `DEMO1001`, which is present in `data/orders.csv`. With `.venv`
active and a valid `GROQ_API_KEY` in `.env`, run:

```sh
refund-agent \
   --email "$(cat examples/refund_request.txt)" \\
   --policy "1. Damaged items may be refunded within 10 days of the order date. 2. The maximum refund amount is INR 20,000." \\
   --thread-id refund-demo-001 \\
   --evaluation-date 2026-10-02 \\
   --orders data/orders.csv
```

The order is looked up in `data/orders.csv`. The app prints the resulting
status and reason. Eligible cases are marked `PENDING_HUMAN_APPROVAL`; the
sample approval handler prints the request rather than issuing a refund.

The CLI accepts these options:

- `--email`: email body to evaluate (required)
- `--policy`: current refund policy text (required)
- `--thread-id`: conversation identifier used for session checkpoints
- `--evaluation-date`: optional date in `YYYY-MM-DD` format
- `--orders`: optional CSV/JSON order-file path override

Use a distinct, stable thread ID for each conversation. Reuse that ID to continue
the same conversation. Set `ORDERS_FILE` in `.env` or pass `--orders` to point
to your own order export.

## Memory Behavior

1. **Short-term:** email, policy, and evaluation date for one invocation.
2. **Session:** LangGraph checkpoints in the SQLite file configured by
    `SESSION_DB`, separated by thread ID. Checkpoints can contain the email body;
    protect and clean up this database according to your data-retention policy.
3. **Long-term:** Milvus stores anonymized category/decision examples. The
    current verified order and policy remain authoritative over retrieved
    historical examples.

To disable Milvus memory, set `LONG_TERM_MEMORY_ENABLED=false`. To use a
different Milvus database or collection, change `MILVUS_URI`, `MILVUS_TOKEN`,
or `MILVUS_COLLECTION` in `.env`.

## Run Tests

```sh
python -m pytest -q
```

## Troubleshooting

- **`refund-agent: command not found`:** activate `.venv` again, or run
   `.venv/bin/refund-agent` directly. If needed, reinstall with
   `python -m pip install -r requirements.txt`.
- **Python version error:** activate the project `.venv` and confirm
   `python --version` is 3.11 or newer.
- **Missing `GROQ_API_KEY`:** set a valid key in `.env`; `load_dotenv()` loads
   `.env`, not `.env.example`.
- **Milvus connection error:** ensure `milvus-standalone` is running and port
   `19530` is reachable. Leave `MILVUS_TOKEN` blank for the unauthenticated local
   instance.
- **First Milvus startup is slow:** FastEmbed downloads its model the first
   time it initializes.