---
description: Audit a view/feature for N+1 queries, missing indexes and slow paths
agent: build
---
Performance audit target: $ARGUMENTS

1. Identify the queries executed (use `CaptureQueriesContext` in a throwaway test or Django debug toolbar settings).
2. Find N+1 patterns, missing `select_related`/`prefetch_related`, unbounded querysets, Python-side aggregation.
3. Check `qs.explain(analyze=True)` on slow queries; propose indexes (`Meta.indexes`, partial/composite) with migration impact.
4. Add a `django_assert_num_queries` regression test.
5. Report before/after query counts.
