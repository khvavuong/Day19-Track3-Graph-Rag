# Day 19 Execution Guide (Data -> GraphRAG Neo4j)

## 1) Quick run (recommended)

```bash
cd graphrag
python scripts/day19_run_pipeline.py --recursive
```

This command will:
- start Docker services (`neo4j`, `backend`, `frontend`, `ollama`),
- precheck `data/`,
- setup Neo4j indexes,
- ingest only 7 target CSV files from `data/`:
  - `movies.csv`
  - `tv_shows.csv`
  - `people.csv`
  - `movie_reviews.csv`
  - `tv_reviews.csv`
  - `orphan_movies.csv`
  - `orphan_tv.csv`
- print post-ingestion stats,
- run Flat vs Graph benchmark (20 questions),
- export reports.

Outputs:
- `reports/day19_benchmark_results.csv`
- `reports/day19_benchmark_summary.md`

## 2) If your machine uses `docker compose` instead of `docker-compose`

```bash
python scripts/day19_run_pipeline.py --compose-cmd "docker compose" --recursive
```

## 3) Run step-by-step manually

```bash
# Start services
docker-compose up -d --build

# Data precheck
docker-compose exec -T backend python scripts/day19_data_precheck.py --data-dir data --recursive

# Neo4j setup and baseline stats
docker-compose exec -T backend python scripts/setup_neo4j.py --test --setup --stats

# Ingest
docker-compose exec -T backend python scripts/ingest_documents.py --file data/movies.csv
docker-compose exec -T backend python scripts/ingest_documents.py --file data/tv_shows.csv
docker-compose exec -T backend python scripts/ingest_documents.py --file data/people.csv
docker-compose exec -T backend python scripts/ingest_documents.py --file data/movie_reviews.csv
docker-compose exec -T backend python scripts/ingest_documents.py --file data/tv_reviews.csv
docker-compose exec -T backend python scripts/ingest_documents.py --file data/orphan_movies.csv
docker-compose exec -T backend python scripts/ingest_documents.py --file data/orphan_tv.csv

# Post-ingest stats
docker-compose exec -T backend python scripts/setup_neo4j.py --stats

# Benchmark with default 20 questions
docker-compose exec -T backend python scripts/day19_benchmark.py
```

## 4) Use custom benchmark questions

Prepare one of:
- `.txt`: each line is one question
- `.csv`: must have a `question` column

Then run:

```bash
docker-compose exec -T backend python scripts/day19_benchmark.py \
  --questions-file reports/day19_questions_template.txt
```

## 5) Notes for deliverables

- In `reports/day19_benchmark_results.csv`, fill manual columns:
  - `expected_answer`
  - `flat_correct_manual`
  - `flat_hallucination_manual`
  - `graph_correct_manual`
  - `graph_hallucination_manual`
  - `hallucination_note`
- Token fields are estimates (`*_tokens_est`) from internal token manager.
- Capture graph screenshots from Neo4j Browser (`http://localhost:7474`).
