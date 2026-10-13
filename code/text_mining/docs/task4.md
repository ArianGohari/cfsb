# Task4 rules run, 2026-09-21

The pipeline runs without an LLM and exports a small, nonempty assertion network from the real corpus. It is not a validated Caco2 regulatory network. Coverage is too low to call the extractor broadly reliable.

## Run and verification

From `code/text_mining/`, use a new output directory:

```sh
uv run litmine run --config config.task4.json --out data/runs/task4-new-run
uv run python -m unittest discover -s tests -q
uv run litmine replay --from-run data/runs/task4-rules-001 --out data/runs/task4-new-replay
```

The completed run is `data/runs/task4-rules-001/`. Its command was:

```sh
uv run litmine run --config config.task4.json --out data/runs/task4-rules-001
```

Exit 0. `INCOMPLETE` is intentional: unresolved screening decisions and annotation gaps remain. Do not run this command over the existing directory.

Artifacts read back and verified:

- `graph.lbug`: LadybugDB, 11 Paper, 11 Document, 3 Entity, 2 Relation and 2 Evidence nodes. The two relations have actual SUBJECT_OF and OBJECT links.
- `papers.parquet`, `documents.parquet`, `entities.parquet`, `relations.parquet`, `evidence.parquet`: all five tables match the export receipt. The relation and evidence tables each contain two rows.
- `graph.svg`: parsed XML with 34 rendered nodes, including the legend, and 19 edges.
- `graph_export.json`: counts, scope, output hashes and rendering receipt.
- `verification.json`: database read-back, table counts, exact evidence spans, code freeze and unchanged corpus hashes.

The verification command was `uv run python tests/verify_task4_run.py data/runs/task4-rules-001`, exit 0. It writes its receipt exclusively and therefore refuses a second write to the same receipt. For a new frozen run, use its new directory.

`uv run python -m unittest discover -s tests -q` passed 143 tests, exit 0. New tests include a verbatim paragraph from PMID33898942, conservative rejection cases, Unicode alignment, explicit attribution, graph scopes and replay. The source paragraph and its PubTator spans are development fixtures, not independent labels.

`data/runs/task4-rules-replay-001/` reproduced entities, relations, evidence and PRISMA counts. The replay ran with `litmine.sources.urlopen` and `litmine.llm.Client` patched to raise on any call. Its `verification.json` records the comparison. Both runs reported zero LLM calls.

## Task1 screening check

`data/runs/task1-screening-audit-001/comparison.json` reassesses the 2,033 archived fulltexts with `clock_cancer`, without calling either relation detector. The old run had 0 included and 2,033 unclear; the new document-scope screen yielded 1,117 candidates and 916 unclear. The command exited 0 and verified the archive's SHA-256 before and after. No Task1 annotation or relation extraction was rerun. This proves that topic screening no longer requires a successful relation pattern; it does not measure screening precision, and the broader candidate criterion is not equivalent to the old molecular-relation criterion.

## What the network says

Both evidence rows come from this sentence in PMID33898942:

> IFI35 was upregulated in both Calu-3 and Caco2 cells but was downregulated in Huh748h.

The emitted assertions are:

- NCBIGene:3430 (IFI35) UPREGULATED_IN Cellosaurus:CVCL_0609 (Calu-3).
- NCBIGene:3430 (IFI35) UPREGULATED_IN Cellosaurus:CVCL_0025 (Caco2).

These are abundance observations, not IFI35-mediated regulation or protein interactions. PubTator's gene identity stays a Gene node; the code does not silently convert it to a protein. `Huh748h` is rejected as an unresolved cell identity because the cell name contains a fused timepoint. The service had assigned that surface form a cell-line identifier; an annotation alone is not sufficient evidence of identity.

Attribution is `unknown`, status is `assertion_pass`. Neither statement becomes an own experiment just because it occurs under Results. Species, experimental condition, compartment and the separate cell-line context field remain null. The explicit cell-line object is preserved; infection, timepoint and comparator are not inherited from nearby paragraphs or the paper title.

This run has zero `auto_pass` and zero own-experiment evidence rows. Choosing an own-experiment graph scope yields no evidence edges. That is a limit of the evidence and rules, not a reason to relabel unknown evidence.

## Measured coverage and precision limits

The run retrieved 29/29 local fulltexts. Eleven met document-level topic and investigation criteria; 18 stayed unclear. All title/abstract decisions stayed unclear because the seed configuration supplies titles but no abstracts.

The 11 annotated documents contained 1,946 anchored mentions across 3,030 parser-defined sentences. Of those sentences, 497 contained at least two mentions of any supported type. Only one sentence produced accepted assertions: two edges from one paper. Paper-level yield is 1/29 (3.45%); sentence yield among annotated documents is 1/3,030 (0.033%). These denominators are coverage measures, not recall or a count of biologically valid opportunities.

PMID33898942 is development data. The remaining 28 papers were reserved before the run in `freeze.json`; none produced an assertion. Held-out paper yield is 0/28. Precision on these papers is undefined because there are no predictions. Recall is unmeasured without reference labels. The two selected-paper assertions have checked literal spans, but a self-check on development text is not an independent precision estimate.

At the evaluation handoff, `code/part1/task4/evaluation/` was absent. No labels from that agent were read or used to change rules. `evaluation.json` therefore says `not_evaluated`. Independent agent judgments must be described as machine-generated reference annotations, not human gold or biological validation.

The extractor and evaluator hashes were frozen before the corpus run. No extraction rule was changed after inspecting the run's held-out coverage. Future changes need a new development/evaluation split and a new run, not a rewrite of these results.

## Evaluation handoff

The evaluator is called by `litmine evaluate`, also by `litmine run` after extraction. The reference format is documented in `litmine/evaluate.py`; it requires paper-level, complete relation annotations, explicit null context fields and train/test assignments. Its manifest leakage check rejects PMID33898942 in the test split for this run.

For evaluation of this graph, the reference file must explicitly set:

```json
{
  "version": 1,
  "prediction_scope": "reported_assertions",
  "annotation_source": "independent automated agent; not human gold",
  "reports": []
}
```

The empty reports list above is a schema illustration, not usable labels. Supply actual test reports. Default scope `attributed` counts only `auto_pass`; `own_experiment` additionally restricts attribution. The new `reported_assertions` scope also counts `assertion_pass`, retaining unknown attribution for strict scoring. Do not score this graph with a silently different prediction scope.

```sh
uv run litmine evaluate --review data/runs/task4-rules-001/review.json \
  --gold /path/to/agent-reference.json --out data/runs/task4-rules-001/evaluation-agent.json
```

No such evaluation has been claimed here. If the independent agent uses sentence-level or incomplete labels, its evaluator must use an explicitly bounded denominator instead of marking whole reports `extraction_complete: true`.

## Changes and boundaries

The real caller chain is CLI/Snakemake -> `engine.run` -> rules Client -> screening -> source annotation -> extraction -> shared candidate validator -> evaluator/exporter. Previously `rules.screen` called relation extraction to establish I1, and `engine.run` skipped annotation and extraction unless fulltext screening included the document. Topic eligibility now has its own rules. Inclusion still requires I1 and I2, and remains a document-level candidate decision.

Profiles:

- `clock_cancer`: default for new rules runs; clock and cancer/checkpoint topic evidence plus an investigation statement.
- `task4_caco2_sarscov2`: Caco2 and SARS-CoV-2/COVID-19 topic evidence plus an investigation statement. It does not assign Caco2 context to extracted relations.
- `legacy_clock`: old relation-coupled screening and narrow extraction. The synthetic rules example selects it explicitly. Legacy LLM mode remains available only when explicitly configured; it was not used here.

`rules.extract` and a direct `rules.screen` call without a profile retain the legacy helper contract. The production Client supplies an explicit profile and uses `extract_assertions` for new profiles.

New profiles recognize complete, simple active/passive assertions for the existing predicates and ACTIVATES/INHIBITS. They also recognize an explicit single analyte reported up/downregulated in enumerated cell lines, with a limited contrast clause. Negation and speculation anywhere in the sentence cause abstention. Ambiguous same-span IDs, overlapping mentions, common family terms and slash-composites are rejected. Many real formulations, indirect effects, coordination, protein complexes and comparisons remain unsupported. The family denylist is not a complete ontology.

Graph scopes are `attributed` (default), `reported_assertions`, and `own_experiment`. Only the explicit reported-assertion scope admits unknown attribution with status `assertion_pass`; other validation problems still prevent acceptance. All rows remain in Parquet. Graph labels and tooltips expose status, attribution and provenance.

PubTator is queried by PMID through public GET requests. No local upload or runtime LLM is used. Fulltext responses with numeric PMC IDs are accepted only when supplied article metadata links the requested PMID to that PMC ID. Cellosaurus annotations retain their namespace. Alignment requires a unique passage or a sufficiently long unique sentence after length-preserving whitespace normalization, with exact entity text. Missing passages, short or duplicate sentences and mismatched mention spans remain gaps. There is no fuzzy alignment, alias propagation or cross-sentence coreference resolution.

The graph contains only two abundance edges, not a reconstructed signaling or PPI network. PubTator entity accuracy, paragraph attribution, screening specificity and biological correctness are not independently established. The 18 unresolved papers and annotation gaps are not negative biological findings.

## Exact changed paths

Existing files edited:

- `code/text_mining/litmine/rules.py`
- `code/text_mining/litmine/engine.py`
- `code/text_mining/litmine/sources.py`
- `code/text_mining/litmine/graph.py`
- `code/text_mining/litmine/evaluate.py`
- `code/text_mining/tests/test_engine.py`
- `code/text_mining/tests/test_rules.py`
- `code/text_mining/tests/test_evaluate.py`
- `code/text_mining/examples/rules/config.json`
- `code/text_mining/README.md`

New code/configuration/test/docs files:

- `code/text_mining/config.task4.json`
- `code/text_mining/tests/test_task4.py`
- `code/text_mining/tests/fixtures/task4_selected.json`
- `code/text_mining/tests/verify_task4_run.py`
- `code/text_mining/docs/task4.md`

New runs only: `archive/text_mining/data/runs/task4-annotation-probe-001/`, `task4-annotation-probe-002/`, `task4-annotation-probe-003/`, `task4-rules-001/`, `task4-rules-replay-001/`, and `task1-screening-audit-001/` under the same runs directory. Probe artifacts retain the failed or partial attempts; none were overwritten. The Task4 corpus and archived Task1 outputs were only read.
