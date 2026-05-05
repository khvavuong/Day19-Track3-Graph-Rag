#!/usr/bin/env python3
"""
Day 19 benchmark runner: Flat RAG (chunk_only) vs GraphRAG (graph_enhanced).
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.token_manager import token_manager
from rag.graph_rag import graph_rag


DEFAULT_QUESTIONS = [
    "What movies starring Keanu Reeves are listed, and who directed them?",
    "Which TV shows created by Vince Gilligan are in the dataset?",
    "Find a movie with high ROI and summarize its genre and main cast.",
    "What are the recommended titles related to The Matrix?",
    "Which actor appears in both movie and TV credits according to this dataset?",
    "List top-rated TV series and their number of seasons.",
    "What is the relationship between Breaking Bad and its recommended shows?",
    "Give me one example where cast and director fields connect two entities.",
    "Which movies have both trailer availability and US watch providers?",
    "What genres are most common among high-vote movies in this corpus?",
    "Who are the creators of popular TV shows and what networks are they on?",
    "Identify one person with directed movies and summarize their profile fields.",
    "What are similar titles for one high-rated movie and one high-rated TV show?",
    "Compare one movie and one TV show by popularity, vote average, and genres.",
    "Find reviews linked to a title and summarize sentiment hints from rating/content.",
    "Which entries include homepage links and what type of media are they?",
    "Show one example of franchise-like relation via collection_name or similar_ids.",
    "Which US certification or US content rating appears for notable titles?",
    "Find a title and link it to available watch_us options in the dataset.",
    "Build a short multi-hop explanation connecting person -> title -> recommendation.",
]


@dataclass
class RunResult:
    answer: str
    latency_sec: float
    sources_count: int
    chunks_used: int
    in_tokens_est: int
    out_tokens_est: int
    total_tokens_est: int
    error: str = ""


def load_questions(path: Path | None) -> list[str]:
    if path is None:
        return DEFAULT_QUESTIONS
    if path.suffix.lower() == ".csv":
        questions: list[str] = []
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                q = (row.get("question") or "").strip()
                if q:
                    questions.append(q)
        return questions
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    return [line for line in lines if line and not line.startswith("#")]


def estimate_tokens(query: str, answer: str) -> tuple[int, int, int]:
    in_tok = token_manager.count_tokens(query)
    out_tok = token_manager.count_tokens(answer)
    return in_tok, out_tok, in_tok + out_tok


def run_single_query(
    question: str,
    retrieval_mode: str,
    top_k: int,
    temperature: float,
    use_multi_hop: bool,
) -> RunResult:
    start = time.perf_counter()
    try:
        response: dict[str, Any] = graph_rag.query(
            user_query=question,
            retrieval_mode=retrieval_mode,
            top_k=top_k,
            temperature=temperature,
            use_multi_hop=use_multi_hop,
        )
        elapsed = time.perf_counter() - start
        answer = str(response.get("response", "") or "")
        sources = response.get("sources", []) or []
        metadata = response.get("metadata", {}) or {}
        chunks_used = int(metadata.get("chunks_used", 0) or 0)
        in_tok, out_tok, total_tok = estimate_tokens(question, answer)
        return RunResult(
            answer=answer,
            latency_sec=elapsed,
            sources_count=len(sources),
            chunks_used=chunks_used,
            in_tokens_est=in_tok,
            out_tokens_est=out_tok,
            total_tokens_est=total_tok,
        )
    except Exception as exc:
        elapsed = time.perf_counter() - start
        return RunResult(
            answer="",
            latency_sec=elapsed,
            sources_count=0,
            chunks_used=0,
            in_tokens_est=0,
            out_tokens_est=0,
            total_tokens_est=0,
            error=str(exc),
        )


def write_markdown_summary(
    output_md: Path,
    rows: list[dict[str, Any]],
    question_count: int,
) -> None:
    flat_ok = sum(1 for r in rows if not r["flat_error"])
    graph_ok = sum(1 for r in rows if not r["graph_error"])
    graph_better_sources = sum(
        1 for r in rows if r["graph_sources_count"] > r["flat_sources_count"]
    )

    avg_flat_latency = sum(r["flat_latency_sec"] for r in rows) / max(1, len(rows))
    avg_graph_latency = sum(r["graph_latency_sec"] for r in rows) / max(1, len(rows))
    flat_tokens = sum(r["flat_total_tokens_est"] for r in rows)
    graph_tokens = sum(r["graph_total_tokens_est"] for r in rows)

    lines = [
        "# Day 19 Benchmark Summary",
        "",
        f"- Total questions: **{question_count}**",
        f"- Flat mode success: **{flat_ok}/{question_count}**",
        f"- Graph mode success: **{graph_ok}/{question_count}**",
        f"- Graph had more sources than Flat: **{graph_better_sources}/{question_count}**",
        f"- Avg Flat latency: **{avg_flat_latency:.2f}s**",
        f"- Avg Graph latency: **{avg_graph_latency:.2f}s**",
        f"- Total Flat token estimate: **{flat_tokens}**",
        f"- Total Graph token estimate: **{graph_tokens}**",
        "",
        "## Notes",
        "- `*_tokens_est` is an approximation from internal token manager.",
        "- Fill manual columns in CSV (`expected_answer`, correctness, hallucination_note) for final grading.",
    ]
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Day 19 Flat vs Graph benchmark")
    parser.add_argument("--questions-file", type=Path, default=None)
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("reports/day19_benchmark_results.csv"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("reports/day19_benchmark_summary.md"),
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--flat-mode", type=str, default="chunk_only")
    parser.add_argument("--graph-mode", type=str, default="graph_enhanced")
    args = parser.parse_args()

    questions = load_questions(args.questions_file)
    if not questions:
        print("ERROR: no questions found")
        return 1

    rows: list[dict[str, Any]] = []
    total = len(questions)
    print(f"Running benchmark for {total} questions...")

    for idx, q in enumerate(questions, start=1):
        print(f"[{idx}/{total}] {q[:90]}")
        flat = run_single_query(
            question=q,
            retrieval_mode=args.flat_mode,
            top_k=args.top_k,
            temperature=args.temperature,
            use_multi_hop=False,
        )
        graph = run_single_query(
            question=q,
            retrieval_mode=args.graph_mode,
            top_k=args.top_k,
            temperature=args.temperature,
            use_multi_hop=True,
        )

        rows.append(
            {
                "question_index": idx,
                "question": q,
                "expected_answer": "",
                "flat_mode": args.flat_mode,
                "flat_answer": flat.answer,
                "flat_latency_sec": round(flat.latency_sec, 3),
                "flat_sources_count": flat.sources_count,
                "flat_chunks_used": flat.chunks_used,
                "flat_in_tokens_est": flat.in_tokens_est,
                "flat_out_tokens_est": flat.out_tokens_est,
                "flat_total_tokens_est": flat.total_tokens_est,
                "flat_correct_manual": "",
                "flat_hallucination_manual": "",
                "flat_error": flat.error,
                "graph_mode": args.graph_mode,
                "graph_answer": graph.answer,
                "graph_latency_sec": round(graph.latency_sec, 3),
                "graph_sources_count": graph.sources_count,
                "graph_chunks_used": graph.chunks_used,
                "graph_in_tokens_est": graph.in_tokens_est,
                "graph_out_tokens_est": graph.out_tokens_est,
                "graph_total_tokens_est": graph.total_tokens_est,
                "graph_correct_manual": "",
                "graph_hallucination_manual": "",
                "graph_error": graph.error,
                "hallucination_note": "",
            }
        )

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    write_markdown_summary(args.output_md, rows, total)
    print(f"Saved benchmark CSV: {args.output_csv}")
    print(f"Saved benchmark summary: {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
