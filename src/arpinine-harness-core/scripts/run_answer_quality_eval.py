#!/usr/bin/env python3
"""Answer-quality eval for context compression (spec 011).

Closes the gap left by run_golden_session_benchmark.py: that benchmark proves
token reduction and asserts governance-outcome identity *by construction*
(on_outcome returns a copy of off_outcome) using a model-free simulate. It never
sends the compressed payload through a real model. This harness does:

    answer_off = model(original_messages)      # compression OFF
    answer_on  = model(compressed_messages)    # compression ON (headroom simulate)

then judges whether compression changed the model's answer, via two signals
(decided in spec 011 answer-quality eval design):

  - embedding similarity  : cosine(answer_off, answer_on) — coarse drift signal
  - LLM-judge prose       : a judge model scores semantic equivalence + quality
                            delta of ON vs OFF

This is the optional real-API-key round-trip. It costs real tokens and needs a
live key, so it is gated: nothing runs without --run, and --estimate prints the
planned call count and spends nothing.

Compression payloads come from the same fixture the benchmark uses
(golden-session/payloads.json), transformed through headroom's
TransformPipeline.simulate() in the managed compression venv (~/.arpinine/
compression-venv), so ON/OFF differ only by the real compression transform.

Usage:
    # No spend — show what the run would do:
    python run_answer_quality_eval.py --estimate

    # Real round-trip (needs ANTHROPIC_API_KEY; pip install anthropic):
    ANTHROPIC_API_KEY=sk-... python run_answer_quality_eval.py --run

    # Limit scope while validating the harness:
    python run_answer_quality_eval.py --run --max-sessions 1

Embedding similarity is optional and pluggable: if `sentence-transformers` is
installed it is used locally (no extra key); otherwise that signal is skipped
with a logged note (the LLM-judge signal still runs). Anthropic has no
embeddings endpoint, which is why this is a separate, optional backend.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import pathlib
import subprocess
import sys
import textwrap

# --- locations -------------------------------------------------------------

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
PAYLOADS = (
    REPO_ROOT
    / ".specify/evals/011-context-compression-governance/golden-session/payloads.json"
)
MANAGED_VENV_PY = pathlib.Path.home() / ".arpinine" / "compression-venv" / "bin" / "python"
RESULTS_DIR = REPO_ROOT / ".specify/evals/011-context-compression-governance"

# Model defaults (claude-api skill: default to claude-opus-4-8, adaptive thinking).
ANSWER_MODEL = "claude-opus-4-8"
JUDGE_MODEL = "claude-opus-4-8"

# The fixed instruction appended to each session's context. Same prompt ON and
# OFF, so any answer divergence is attributable to the compression transform.
GOVERNANCE_QUESTION = (
    "Based only on the repository scan context above, summarize the current "
    "state of the modules (counts by status, notable owners) and recommend the "
    "single next governed action. Be specific and concise."
)

# Verdict schema for the LLM judge (structured output).
VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "equivalent": {
            "type": "boolean",
            "description": "True if the two answers convey the same governance-relevant facts and recommendation.",
        },
        "quality_delta": {
            "type": "integer",
            "enum": [-2, -1, 0, 1, 2],
            "description": "Quality of ON minus OFF. Negative means compression degraded the answer.",
        },
        "divergences": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Concrete facts present/correct in one answer but not the other.",
        },
        "rationale": {"type": "string"},
    },
    "required": ["equivalent", "quality_delta", "divergences", "rationale"],
    "additionalProperties": False,
}


# --- compression (managed venv) -------------------------------------------

_COMPRESS_SNIPPET = """
import json, sys, headroom as hr
doc = json.load(sys.stdin)
payloads = doc["payloads"]
model = doc.get("model", "claude-sonnet-4-5-20250929")
limit = int(doc.get("model_limit", 200000))
pipe = hr.TransformPipeline(config=hr.HeadroomConfig(intercept_tool_results=True))
out = []
for messages in payloads:
    res = pipe.simulate(messages, model=model, model_limit=limit)
    out.append({
        "on_messages": res.messages,
        "tokens_before": int(res.tokens_before),
        "tokens_after": int(res.tokens_after),
    })
json.dump(out, sys.stdout)
"""


def compress_sessions(doc: dict) -> list[dict]:
    """Run headroom simulate in the managed venv; return per-session compressed payloads."""
    if not MANAGED_VENV_PY.exists():
        raise SystemExit(
            f"managed compression venv not found at {MANAGED_VENV_PY}\n"
            "Run /at-init (compression bootstrap) or a session with compression "
            "enabled to provision it."
        )
    proc = subprocess.run(
        [str(MANAGED_VENV_PY), "-c", _COMPRESS_SNIPPET],
        input=json.dumps(doc),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(f"compression subprocess failed:\n{proc.stderr}")
    return json.loads(proc.stdout)


# --- message conversion ----------------------------------------------------


def to_anthropic_messages(generic: list[dict], question: str) -> list[dict]:
    """Flatten headroom's generic {role, content} stream into Anthropic messages.

    The fixture uses a 'tool' role that the Messages API doesn't accept directly,
    so tool output is folded into a user turn as labeled context. A final user
    turn carries the fixed governance question.
    """
    parts = []
    for m in generic:
        role = m.get("role", "user")
        content = m.get("content", "")
        if not isinstance(content, str):
            content = json.dumps(content)
        if role == "tool":
            parts.append(f"[tool output]\n{content}")
        elif role == "assistant":
            parts.append(f"[assistant]\n{content}")
        else:
            parts.append(f"[user]\n{content}")
    context = "\n\n".join(parts)
    return [{"role": "user", "content": f"{context}\n\n---\n\n{question}"}]


# --- model calls -----------------------------------------------------------


def make_client():
    try:
        import anthropic  # noqa: F401
    except ImportError:
        raise SystemExit("pip install anthropic  (required for --run)")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("set ANTHROPIC_API_KEY for --run")
    import anthropic

    return anthropic.Anthropic()


def model_answer(client, messages: list[dict]) -> str:
    """One answer from the answer model. Streams (large input) and adaptive thinking."""
    with client.messages.stream(
        model=ANSWER_MODEL,
        max_tokens=2000,
        thinking={"type": "adaptive"},
        messages=messages,
    ) as stream:
        msg = stream.get_final_message()
    return "".join(b.text for b in msg.content if b.type == "text")


def llm_judge(client, off: str, on: str) -> dict:
    """Judge ON vs OFF answers for semantic equivalence + quality delta."""
    prompt = textwrap.dedent(
        f"""\
        Two assistants answered the same governance question from the same
        repository-scan context. ANSWER_OFF used the full context; ANSWER_ON
        used a context that was losslessly compressed before the model saw it.
        Judge whether compression changed the answer.

        ANSWER_OFF:
        {off}

        ANSWER_ON:
        {on}

        Compare them on governance-relevant facts (counts, statuses, owners) and
        the recommended next action. Report your verdict via the tool/schema."""
    )
    resp = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=1500,
        thinking={"type": "adaptive"},
        output_config={"format": {"type": "json_schema", "schema": VERDICT_SCHEMA}},
        messages=[{"role": "user", "content": prompt}],
    )
    text = next(b.text for b in resp.content if b.type == "text")
    return json.loads(text)


# --- embedding similarity (optional, pluggable) ----------------------------


def get_embedder():
    """Return an embed(texts)->vectors fn, or None if no backend is available.

    Anthropic has no embeddings endpoint; this uses a local sentence-transformers
    model when installed (no extra key). Swap in Voyage AI here if preferred.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return lambda texts: model.encode(texts, normalize_embeddings=True).tolist()


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


# --- main ------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--run", action="store_true", help="execute the real round-trip (spends tokens)")
    g.add_argument("--estimate", action="store_true", help="print planned calls; spend nothing")
    ap.add_argument("--max-sessions", type=int, default=None, help="limit sessions (validation)")
    ap.add_argument("--payloads", type=pathlib.Path, default=PAYLOADS)
    args = ap.parse_args()

    doc = json.loads(args.payloads.read_text())
    n_sessions = len(doc["payloads"])
    if args.max_sessions:
        doc = {**doc, "payloads": doc["payloads"][: args.max_sessions]}
        n_sessions = len(doc["payloads"])

    if args.estimate:
        # 2 answer calls + 1 judge call per session.
        print(f"sessions:        {n_sessions}")
        print(f"answer calls:    {2 * n_sessions}  (OFF + ON per session, {ANSWER_MODEL})")
        print(f"judge calls:     {n_sessions}  ({JUDGE_MODEL})")
        print(f"total API calls: {3 * n_sessions}")
        print("embeddings:      local (sentence-transformers) — no API spend")
        print("\nNo tokens spent. Re-run with --run + ANTHROPIC_API_KEY for the round-trip.")
        return 0

    client = make_client()
    embed = get_embedder()
    if embed is None:
        print("note: sentence-transformers not installed — embedding-sim signal skipped "
              "(pip install sentence-transformers to enable)", file=sys.stderr)

    compressed = compress_sessions(doc)
    rows = []
    for i, (generic, comp) in enumerate(zip(doc["payloads"], compressed)):
        off_msgs = to_anthropic_messages(generic, GOVERNANCE_QUESTION)
        on_msgs = to_anthropic_messages(comp["on_messages"], GOVERNANCE_QUESTION)

        print(f"[session {i}] answering OFF/ON …", file=sys.stderr)
        off = model_answer(client, off_msgs)
        on = model_answer(client, on_msgs)

        print(f"[session {i}] judging …", file=sys.stderr)
        verdict = llm_judge(client, off, on)

        sim = None
        if embed is not None:
            va, vb = embed([off, on])
            sim = round(cosine(va, vb), 4)

        rows.append({
            "session": i,
            "tokens_before": comp["tokens_before"],
            "tokens_after": comp["tokens_after"],
            "reduction_pct": round(100 * (1 - comp["tokens_after"] / comp["tokens_before"]), 1),
            "embedding_sim": sim,
            "equivalent": verdict["equivalent"],
            "quality_delta": verdict["quality_delta"],
            "divergences": verdict["divergences"],
            "rationale": verdict["rationale"],
        })

    write_results(rows)
    return 0


def write_results(rows: list[dict]) -> None:
    out_json = RESULTS_DIR / "answer-quality-results.json"
    out_md = RESULTS_DIR / "answer-quality-results.md"
    out_json.write_text(json.dumps(rows, indent=2))

    n = len(rows)
    equiv = sum(1 for r in rows if r["equivalent"])
    sims = [r["embedding_sim"] for r in rows if r["embedding_sim"] is not None]
    avg_sim = round(sum(sims) / len(sims), 4) if sims else None
    avg_delta = round(sum(r["quality_delta"] for r in rows) / n, 2) if n else 0
    worst_delta = min((r["quality_delta"] for r in rows), default=0)

    lines = [
        "# Answer-Quality Eval — Context Compression (Spec 011)",
        "",
        "Real-API-key round-trip: same governance question answered ON vs OFF "
        "compression, judged for semantic equivalence + quality delta.",
        "",
        f"- Model: `{ANSWER_MODEL}` (answers), `{JUDGE_MODEL}` (judge)",
        f"- Sessions: {n}",
        f"- Equivalent answers: {equiv}/{n}",
        f"- Avg quality delta (ON−OFF): {avg_delta}  (worst: {worst_delta})",
        f"- Avg embedding similarity: {avg_sim if avg_sim is not None else 'n/a (backend not installed)'}",
        "",
        "| session | reduction % | equiv | quality Δ | embed sim | divergences |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        sim = r["embedding_sim"] if r["embedding_sim"] is not None else "—"
        div = "; ".join(r["divergences"]) if r["divergences"] else "—"
        lines.append(
            f"| {r['session']} | {r['reduction_pct']} | "
            f"{'✅' if r['equivalent'] else '❌'} | {r['quality_delta']} | {sim} | {div} |"
        )
    out_md.write_text("\n".join(lines) + "\n")
    print(f"wrote {out_md}")
    print(f"wrote {out_json}")


if __name__ == "__main__":
    raise SystemExit(main())
