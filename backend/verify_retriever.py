"""
verify_retriever.py -- Phase 2 verification script for SimpleRetriever.

Run from the backend/ directory:
    python verify_retriever.py

Tests five diagnostic queries and prints retrieved document titles and scores.
Makes NO external API calls -- pure local JSON retrieval only.
"""
import sys
from pathlib import Path

# Ensure backend root is on the path so rag.* imports resolve
sys.path.insert(0, str(Path(__file__).parent))

from rag.simple_retriever import SimpleRetriever

SEPARATOR = "-" * 70

TEST_QUERIES = [
    {
        "label": "Query 1 - Bearing fault",
        "query": "high vibration metallic noise bearing",
        "top_k": 3,
    },
    {
        "label": "Query 2 - Engine/motor overheating",
        "query": "high engine temperature low pressure",
        "top_k": 3,
    },
    {
        "label": "Query 3 - Pump cavitation",
        "query": "erratic pump pressure high noise",
        "top_k": 3,
    },
    {
        "label": "Query 4 - Shaft misalignment",
        "query": "shaft vibration misalignment",
        "top_k": 3,
    },
    {
        "label": "Query 5 - Gearbox oil starvation",
        "query": "gearbox high temperature oil starvation",
        "top_k": 3,
    },
]

# For queries where multiple docs are legitimately relevant, we check that
# the expected doc appears in the top-3 results (not strictly top-1).
# Query 1: bearing, lubrication, and low-oil docs all discuss metallic noise+vibration,
#           so top-3 containment is the correct assertion.
EXPECTED_IN_TOP3 = [
    "bearing_degradation",     # Query 1 -- must appear in top-3
    "engine_overheating",      # Query 2 -- must be top-1 (unique "engine" title term)
    "pump_cavitation",         # Query 3 -- must be top-1 (unique "cavitation" title term)
    "shaft_misalignment",      # Query 4 -- must be top-1 (unique "misalignment" title term)
    "gearbox_overheating",     # Query 5 -- must be top-1 (unique "gearbox" title term)
]

# For queries 2-5 the expected doc must also be top-1
MUST_BE_TOP1 = {1, 2, 3, 4}   # 0-indexed


def main():
    print(SEPARATOR)
    print("VitalMech -- SimpleRetriever Verification")
    print("Phase 2 | No IBM/Granite API calls made")
    print(SEPARATOR)

    retriever = SimpleRetriever()
    n_docs = len(retriever._docs)
    print(f"Knowledge base loaded: {n_docs} documents\n")

    if n_docs == 0:
        print("ERROR: No documents loaded. Check backend/knowledge/mechanical_faults.json")
        sys.exit(1)

    all_passed = True

    for i, test in enumerate(TEST_QUERIES):
        print(f"\n{test['label']}")
        print(f"  Query : \"{test['query']}\"")
        print(f"  top_k : {test['top_k']}")
        print()

        results = retriever.retrieve_scored(test["query"], top_k=test["top_k"])

        if not results:
            print("  [WARN] No results returned")
            all_passed = False
            continue

        for rank, doc in enumerate(results, start=1):
            print(f"  [{rank}] {doc.title}")
            print(f"       id: {doc.doc_id}  |  score: {doc.score}")

        # Pass/fail check
        expected = EXPECTED_IN_TOP3[i]
        result_ids = [r.doc_id for r in results]
        in_top3 = expected in result_ids

        if i in MUST_BE_TOP1:
            # For these queries the expected doc must be the top-1 result
            passed = results[0].doc_id == expected
            label = "top-1"
        else:
            # For query 1 (bearing), we accept top-3 containment
            passed = in_top3
            label = "top-3 containment"

        if passed:
            print(f"\n  [PASS] '{expected}' found in results ({label} check)")
        else:
            print(f"\n  [FAIL] '{expected}' not found -- got {result_ids}")
            all_passed = False

        print(SEPARATOR)

    # Summary
    print()
    if all_passed:
        print("ALL 5 TESTS PASSED [OK]")
    else:
        print("SOME TESTS FAILED -- review retrieval scores above")

    print()
    print("Confirmed: no IBM Granite, watsonx.ai, ChromaDB, or")
    print("sentence-transformers calls were made during this test.")
    print(SEPARATOR)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
