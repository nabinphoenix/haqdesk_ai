"""
Near-Domain Confusion Test for HaqDesk AI RAG System.

Tests the harder failure mode: queries about one TechSuru product/policy
that might retrieve a similar-but-wrong TechSuru chunk. This validates
whether the LLM confidently answers with the WRONG in-domain chunk
(dangerous) or notices the mismatch.

Each test case has:
- A deliberately ambiguous query designed to retrieve a confusable chunk
- The CORRECT chunk ID / topic it should answer from
- The WRONG chunk that could be retrieved due to similar wording
"""
import asyncio
import sys
import io
import os
import time
import json
import logging

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("eval_near_domain")
logger.setLevel(logging.INFO)

from app.services.rag_service import rag_service
from app.prompts.customer_reply_prompt import build_system_prompt
from app.services.llm_gateway import llm_gateway

# ============================================================================
# NEAR-DOMAIN CONFUSION TEST CASES
#
# Each test probes whether the retriever gets the RIGHT chunk and whether
# the LLM answers correctly even if the WRONG chunk is retrieved.
# ============================================================================
NEAR_DOMAIN_TESTS = [
    {
        "id": 1,
        "query": "Does my second-hand laptop have warranty?",
        "lang": "english",
        "correct_topic": "Second-hand warranty (limited service warranty, depends on condition)",
        "confusable_topic": "New product warranty (manufacturer warranty)",
        "key_distinction": "Second-hand = limited SERVICE warranty; New = MANUFACTURER warranty",
        "correct_keywords": ["second-hand", "refurbished", "limited", "service warranty", "condition", "company policy"],
        "wrong_keywords": ["manufacturer warranty", "brand", "supplier policy"],
    },
    {
        "id": 2,
        "query": "naya laptop ko warranty kati lamo huncha?",
        "lang": "romanized_nepali",
        "correct_topic": "New product warranty period (varies by brand/category)",
        "confusable_topic": "Second-hand warranty period",
        "key_distinction": "New products = manufacturer warranty; period varies by brand. Should NOT mention 'limited service warranty'",
        "correct_keywords": ["brand", "category", "invoice", "manufacturer", "product details"],
        "wrong_keywords": ["limited service warranty", "refurbished"],
    },
    {
        "id": 3,
        "query": "Can I return this laptop and get my money back?",
        "lang": "english",
        "correct_topic": "Return policy AND Refund policy (two separate policies)",
        "confusable_topic": "Exchange policy (different from refund)",
        "key_distinction": "Return = depends on condition/category/invoice; Refund = not automatic, needs inspection; Exchange = different process",
        "correct_keywords": ["return", "refund", "inspection", "condition", "invoice"],
        "wrong_keywords": ["exchange"],
    },
    {
        "id": 4,
        "query": "repair garda kati kharcha lagcha?",
        "lang": "romanized_nepali",
        "correct_topic": "Repair cost (depends on diagnosis, parts, condition)",
        "confusable_topic": "Diagnostic charges (separate fee before repair)",
        "key_distinction": "Repair cost = overall cost after diagnosis; Diagnostic charge = fee just for inspection",
        "correct_keywords": ["repair cost", "diagnosis", "parts", "device condition", "estimate", "inspection"],
        "wrong_keywords": ["diagnostic charge", "before inspection"],
    },
    {
        "id": 5,
        "query": "Can you recover my lost data from a broken phone?",
        "lang": "english",
        "correct_topic": "Data recovery services (may be available, not guaranteed)",
        "confusable_topic": "Data backup before repair (customer should backup first)",
        "key_distinction": "Recovery = TechSuru attempts to recover lost data; Backup = customer's responsibility BEFORE submitting",
        "correct_keywords": ["data recovery", "device condition", "type of data loss", "not guaranteed"],
        "wrong_keywords": ["back up", "remove", "before submitting"],
    },
    {
        "id": 6,
        "query": "मेरो फोनको ब्याट्री warranty मा cover हुन्छ?",
        "lang": "nepali",
        "correct_topic": "Battery warranty coverage (depends on manufacturer policy, usage pattern)",
        "confusable_topic": "General warranty exclusions (physical damage, liquid damage, etc.)",
        "key_distinction": "Battery warranty = specific policy depending on manufacturer; General exclusions = broader list of what's NOT covered",
        "correct_keywords": ["battery", "manufacturer policy", "usage pattern"],
        "wrong_keywords": ["physical damage", "liquid damage", "unauthorized repairs"],
    },
    {
        "id": 7,
        "query": "warranty repair pachi restart huncha ki same period continue huncha?",
        "lang": "romanized_nepali",
        "correct_topic": "Warranty continuation after repair (original period continues, doesn't restart)",
        "confusable_topic": "Warranty period length (varies by product/brand)",
        "key_distinction": "Continuation = original period continues; Period = how long it lasts initially",
        "correct_keywords": ["continue", "restart", "original warranty", "manufacturer", "company policy"],
        "wrong_keywords": ["varies by product", "check the invoice"],
    },
    {
        "id": 8,
        "query": "Can I exchange my phone for a different model instead of getting it repaired?",
        "lang": "english",
        "correct_topic": "Exchange policy (must be eligible, acceptable condition, branch approval)",
        "confusable_topic": "Return/refund policy OR repair services",
        "key_distinction": "Exchange = swap for different product; Return = give back for refund; Repair = fix the same device",
        "correct_keywords": ["exchange", "eligible", "condition", "approved", "branch"],
        "wrong_keywords": ["refund", "repair", "diagnosis", "technician"],
    },
    {
        "id": 9,
        "query": "paani pareko phone repair hunchha?",
        "lang": "romanized_nepali",
        "correct_topic": "Water-damaged device repair (may inspect but not guaranteed)",
        "confusable_topic": "General repair services OR repair risk notice",
        "key_distinction": "Water damage = specific caveat that repair success is NOT guaranteed",
        "correct_keywords": ["water-damaged", "not guaranteed", "inspect"],
        "wrong_keywords": ["registered", "diagnosed", "repair ticket"],
    },
    {
        "id": 10,
        "query": "second-hand phone kineko invoice haraye bhane warranty claim garna milcha?",
        "lang": "romanized_nepali",
        "correct_topic": "Lost invoice + warranty claim (contact branch, verification through records, not guaranteed)",
        "confusable_topic": "Invoice required for warranty (yes, keep invoice) — similar but different answer",
        "key_distinction": "Lost invoice = may verify through records but NOT guaranteed; Invoice required = yes, keep it",
        "correct_keywords": ["contact the branch", "verification", "company records", "not guaranteed"],
        "wrong_keywords": ["keep the invoice", "proof of purchase"],
    },
]

# ============================================================================
# Multilingual decline/uncertainty signals
# ============================================================================
UNCERTAINTY_SIGNALS = [
    # English
    "may", "depends on", "depending on", "varies", "subject to",
    "not guaranteed", "please contact", "confirm", "check",
    # Romanized Nepali
    "milxa", "depend", "nimtya", "sakchha", "sakdaina",
    "huna sakcha", "branch ma", "contact garne",
    # Devanagari
    "निर्भर", "सम्पर्क", "शाखा", "सम्भव",
]


def grade_response(test_case, response_text, retrieved_chunks):
    """
    Grade whether the LLM response is:
    - CORRECT: Uses the right chunk's information
    - WRONG_CHUNK: Confidently answers using the wrong-but-similar chunk
    - HEDGED: Gives a safe hedged/generic answer (acceptable)
    - UNCLEAR: Can't determine
    """
    resp_lower = response_text.lower()

    # Count correct vs wrong keyword hits
    correct_hits = sum(1 for kw in test_case["correct_keywords"] if kw.lower() in resp_lower)
    wrong_hits = sum(1 for kw in test_case["wrong_keywords"] if kw.lower() in resp_lower)

    # Check if response hedges appropriately
    hedge_count = sum(1 for sig in UNCERTAINTY_SIGNALS if sig.lower() in resp_lower)

    # Check what the top retrieved chunk actually covers
    top_chunk = retrieved_chunks[0]["content"][:200] if retrieved_chunks else ""

    if correct_hits >= 2 and wrong_hits == 0:
        return "✅ CORRECT", correct_hits, wrong_hits, hedge_count
    elif wrong_hits >= 2 and correct_hits == 0:
        return "❌ WRONG CHUNK (confidently wrong)", correct_hits, wrong_hits, hedge_count
    elif wrong_hits >= 1 and correct_hits == 0:
        return "⚠️ LIKELY WRONG (some wrong signals)", correct_hits, wrong_hits, hedge_count
    elif hedge_count >= 2 and wrong_hits == 0:
        return "🟡 HEDGED (safe generic)", correct_hits, wrong_hits, hedge_count
    elif correct_hits >= 1:
        return "✅ MOSTLY CORRECT", correct_hits, wrong_hits, hedge_count
    else:
        return "🔍 UNCLEAR (manual review needed)", correct_hits, wrong_hits, hedge_count


async def run_near_domain_evaluation():
    print("=" * 80)
    print("    HAQDESK AI — NEAR-DOMAIN CONFUSION TEST (SIMILAR-BUT-WRONG CHUNKS)")
    print("=" * 80)
    print(f"\nRunning {len(NEAR_DOMAIN_TESTS)} deliberately confusable queries...")
    print("Each query targets a specific policy that has a near-identical sibling.\n")

    # Pre-warm
    print("[WARMUP] Loading embedding model...")
    _ = rag_service.embed_text("warmup")
    print("[WARMUP] Ready.\n")

    results = []

    for test in NEAR_DOMAIN_TESTS:
        tid = test["id"]
        query = test["query"]
        lang = test["lang"]

        print(f"{'='*80}")
        print(f"TEST [{tid}]: '{query}'")
        print(f"  Language:           {lang}")
        print(f"  Correct topic:      {test['correct_topic']}")
        print(f"  Confusable topic:   {test['confusable_topic']}")
        print(f"  Key distinction:    {test['key_distinction']}")

        # Step 1: Retrieve top-3 chunks
        chunks = rag_service.retrieve_chunks(query, business_id=1, top_k=3)
        top_score = chunks[0]["similarity"] if chunks else 0.0

        print(f"\n  RETRIEVAL:")
        for i, c in enumerate(chunks[:3]):
            preview = c["content"][:150].replace('\n', ' ')
            print(f"    [{i+1}] Score={c['similarity']:.4f} | \"{preview}...\"")

        # Step 2: Build prompt + call LLM (same logic as rag_service.query)
        if chunks and top_score >= 0.45:
            context = "\n\n---\n\n".join([
                f"[Page {c['page_number']}] {c['content']}" for c in chunks
            ])
        else:
            context = "No specific policy document match found."

        system_prompt = build_system_prompt(
            context=context,
            mode="auto",
            language=lang,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]

        try:
            t0 = time.time()
            llm_result = await llm_gateway.complete(messages=messages, max_tokens=300)
            latency = (time.time() - t0) * 1000
            response_text = llm_result["content"]
            model = llm_result.get("model", "unknown")
        except Exception as e:
            response_text = f"[LLM ERROR: {e}]"
            latency = 0
            model = "error"

        print(f"\n  LLM RESPONSE ({model}, {latency:.0f}ms):")
        print(f"    \"{response_text}\"")

        # Step 3: Grade
        verdict, correct_hits, wrong_hits, hedge_count = grade_response(test, response_text, chunks)
        print(f"\n  GRADING:")
        print(f"    Correct keyword hits: {correct_hits}/{len(test['correct_keywords'])}")
        print(f"    Wrong keyword hits:   {wrong_hits}/{len(test['wrong_keywords'])}")
        print(f"    Hedge signals:        {hedge_count}")
        print(f"    VERDICT:              {verdict}")
        print()

        results.append({
            "id": tid,
            "query": query,
            "score": top_score,
            "response": response_text,
            "verdict": verdict,
            "correct_hits": correct_hits,
            "wrong_hits": wrong_hits,
        })

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "=" * 80)
    print("                         SUMMARY")
    print("=" * 80)

    correct = sum(1 for r in results if "CORRECT" in r["verdict"])
    wrong = sum(1 for r in results if "WRONG" in r["verdict"])
    hedged = sum(1 for r in results if "HEDGED" in r["verdict"])
    unclear = sum(1 for r in results if "UNCLEAR" in r["verdict"])

    print(f"\n  Total tests:           {len(results)}")
    print(f"  ✅ Correct:             {correct}")
    print(f"  ❌ Wrong chunk used:    {wrong}")
    print(f"  🟡 Hedged (safe):       {hedged}")
    print(f"  🔍 Unclear:             {unclear}")
    print(f"\n  Accuracy:              {correct}/{len(results)} ({100*correct/len(results):.0f}%)")
    print(f"  Safety (correct+hedged): {correct+hedged}/{len(results)} ({100*(correct+hedged)/len(results):.0f}%)")
    print(f"  Dangerous (wrong):     {wrong}/{len(results)} ({100*wrong/len(results):.0f}%)")

    if wrong > 0:
        print(f"\n  ⚠️  DANGEROUS CASES (confidently wrong, in-domain):")
        for r in results:
            if "WRONG" in r["verdict"]:
                print(f"    Test [{r['id']}]: '{r['query']}'")
                print(f"      Response: \"{r['response'][:200]}...\"")
                print()

    print("\n" + "=" * 80)
    if wrong == 0:
        print("  CONCLUSION: LLM handles near-domain confusion safely.")
        print("  Threshold 0.45 is SAFE for production traffic.")
    elif wrong <= 2:
        print("  CONCLUSION: Minor near-domain confusion risk.")
        print("  Consider prompt improvements for distinguishing similar policies.")
    else:
        print("  CONCLUSION: SIGNIFICANT near-domain confusion risk.")
        print("  Prompt and/or retrieval need architectural changes.")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_near_domain_evaluation())
