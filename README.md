# BD-AgriKG

A knowledge graph of crop suitability and productivity in Bangladesh, and
the first English and Bangla execution-based Text2Cypher benchmark built on
it. Companion release of the paper

> Md. Aukerul Moin Shuvo and Md. Nazrul Islam Mondal. 2026. BD-AgriKG: A
> Knowledge Graph and Bilingual Text2Cypher Benchmark for Crop Suitability
> and Productivity in Bangladesh. In *Proceedings of the Third Workshop on
> Knowledge Graphs and Agentic Systems Interplay (NORA 2026)*, AACL-IJCNLP
> 2026. Department of Computer Science & Engineering, Rajshahi University
> of Engineering & Technology (RUET).

The graph joins five public government sources on one administrative spine
keyed by OCHA COD-AB place codes (8 divisions, 64 districts, 507 upazilas):
BARC land suitability for 16 crops, BAMIS agro-meteorological thresholds,
the BBS crop calendar, SRDI soil associations, and a district production
panel for 12 crop years (2013-14 to 2024-25) extracted from ten BBS
yearbook editions. The benchmark has 460 questions from 26 templates, each
with an executable gold Cypher query and its executed answer, in English
and in Bangla.

## Versions

- **v1.0** is the graph and benchmark exactly as evaluated in the paper
  (13 September 2026).
- **v1.1** (7 October 2026) corrects extraction defects found in a
  post-review audit. Questions, parameters and gold queries are unchanged;
  the corrected data changes the executed gold answer of 33 items and
  retires 12 whose query returns nothing on the corrected graph.
  `CHANGELOG.md` lists every change; `benchmark/v1/CHANGES_v1.1.md` lists
  the items.

Both graphs are included (`data/kg/v1.0`, `data/kg/v1.1`). Every number in
the paper is on v1.0.

## Layout

- `data/kg/v1.0`, `data/kg/v1.1`: node and relationship tables of the
  property graph (CSV); `src/load_neo4j.py` loads either
- `data/raw`: source tables (BARC crop zoning, BAMIS agro-meteorology,
  SRDI soils, BBS crop calendar, corrected crop-pest table)
- `data/gazetteer.csv`: the P-code spine, from OCHA COD-AB
- `data/bbs_extraction`: per-edition yearbook extractions and their
  validation reports
- `data/bbs_yearbook_urls.md`: where to download the yearbook PDFs (not
  bundled, 200 MB)
- `src`: construction pipeline (gazetteer, graph build, yearbook
  extraction, cross-edition consensus panel, Neo4j loader)
- `benchmark`: templates, generator, and `v1/` with `benchmark.jsonl`
  (v1.0 gold), `benchmark_v1.1.jsonl` (both golds), the schema prompt,
  and the Bangla validation sheets
- `eval`: evaluation harness (execution accuracy, strict and lenient),
  model adapters (Amazon Bedrock, local Ollama), the execution-feedback
  retry, re-scoring, significance tests and error taxonomy
- `eval/results`: raw per-item outputs of every reported run;
  `eval/results/camera` holds the same runs re-scored with the corrected
  grader used in the final paper
- `docs/DATA_NOTES.md`: data quality notes and the audit record

## Reproduce

1. `docker compose up -d` (Neo4j 5; default auth in `docker-compose.yml`)
2. `pip install -r requirements.txt`
3. `KG_DIR=data/kg/v1.0 python src/load_neo4j.py --wipe` (or `v1.1`)
4. `python eval/run_eval.py --adapter gold --lang en` should score 460/460
   on v1.0; on v1.1 it scores 415/460, the items listed in
   `benchmark/v1/CHANGES_v1.1.md` being the difference
5. Model runs: put credentials in `.env` (see `.env.example`) and run
   `python eval/run_eval.py --adapter bedrock:<model-id> --lang bn`; a
   local model served by Ollama runs with `--adapter ollama:<model>`
6. `python eval/run_retry.py --adapter <same spec> --lang bn` for the
   execution-feedback retry; `python eval/rescore_v1_graders.py`,
   `eval/gap_tests.py` and `eval/error_analysis.py` rebuild the tables

To rebuild the graph from the sources: `python src/build_gazetteer.py`,
`python src/build_kg.py`, download the yearbooks, then
`python src/extract_bbs.py 2016 ... 2025` and
`python src/build_yield_panel.py`.

## Licenses

Code is released under the MIT License (`LICENSE`). The derived data
(graph tables, production panel, benchmark) is released under CC BY 4.0
(`LICENSE-DATA.md`). The underlying sources are public publications of
the Government of Bangladesh (BBS, BARC, BAMIS, SRDI) and OCHA COD-AB
(CC BY-IGO); the yearbook PDFs are not redistributed here.

## Contact

Md. Aukerul Moin Shuvo, 2204103003@student.ruet.ac.bd
