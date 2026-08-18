import sys
import io
import os
import json
import logging
import statistics

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.rag_service import rag_service
from app.services.nepali_normalizer import get_embedding_input

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("eval_retrieval")

# Comprehensive Expanded Evaluation Dataset (75 Total Queries)
EXPANDED_EVAL_DATASET = [
    # ================= ENGLISH IN-DOMAIN QUERIES (20 Queries) =================
    {"query": "Where is the head office of TechSuru located?", "lang": "english", "keywords": ["New Baneshwor", "Kathmandu", "head office"], "is_relevant": True},
    {"query": "Who owns and manages TechSuru?", "lang": "english", "keywords": ["Nabin Nepali"], "is_relevant": True},
    {"query": "Does TechSuru sell third-hand products?", "lang": "english", "keywords": ["DOES NOT sell third-hand", "third-hand"], "is_relevant": True},
    {"query": "Can I sell my old laptop to TechSuru?", "lang": "english", "keywords": ["second-hand laptops", "buys", "inspection"], "is_relevant": True},
    {"query": "What payment methods does TechSuru accept?", "lang": "english", "keywords": ["cash", "bank transfer", "mobile banking", "QR payment"], "is_relevant": True},
    {"query": "How many branches does TechSuru have across Nepal?", "lang": "english", "keywords": ["seven branches", "7 branches"], "is_relevant": True},
    {"query": "Does TechSuru issue VAT invoices?", "lang": "english", "keywords": ["VAT invoices", "applicable"], "is_relevant": True},
    {"query": "What products does TechSuru sell?", "lang": "english", "keywords": ["laptops", "smartphones", "accessories", "printers"], "is_relevant": True},
    {"query": "Does TechSuru provide warranty on second hand laptops?", "lang": "english", "keywords": ["warranty", "second-hand"], "is_relevant": True},
    {"query": "How long does delivery take across Nepal?", "lang": "english", "keywords": ["delivery time", "location", "logistics"], "is_relevant": True},
    {"query": "Does TechSuru provide device repair services?", "lang": "english", "keywords": ["repair", "technician", "devices"], "is_relevant": True},
    {"query": "Can businesses request official quotations from TechSuru?", "lang": "english", "keywords": ["quotations", "businesses"], "is_relevant": True},
    {"query": "What is TechSuru's device health score policy?", "lang": "english", "keywords": ["health score", "battery", "condition"], "is_relevant": True},
    {"query": "Does TechSuru sell original brand new laptops?", "lang": "english", "keywords": ["brand new", "genuine"], "is_relevant": True},
    {"query": "What are the business operating hours of TechSuru?", "lang": "english", "keywords": ["hours", "open", "contact"], "is_relevant": True},
    {"query": "Does TechSuru provide annual maintenance contracts for corporate clients?", "lang": "english", "keywords": ["annual maintenance", "corporate", "contracts"], "is_relevant": True},
    {"query": "Can I return a defective laptop within the return period?", "lang": "english", "keywords": ["return", "refund", "defective"], "is_relevant": True},
    {"query": "What happens if my repaired device faces issues under warranty?", "lang": "english", "keywords": ["warranty", "repair", "inspection"], "is_relevant": True},
    {"query": "Does TechSuru offer trade-in or exchange options for old phones?", "lang": "english", "keywords": ["trade-in", "exchange", "second-hand"], "is_relevant": True},
    {"query": "How can I contact TechSuru customer support team?", "lang": "english", "keywords": ["9829592158", "admin.haqdesk.ai@gmail.com", "contact"], "is_relevant": True},

    # ================= DEVANAGARI NEPALI IN-DOMAIN QUERIES (20 Queries) =================
    {"query": "टेकसरुको मुख्य कार्यालय कहाँ छ?", "lang": "nepali", "keywords": ["New Baneshwor", "Kathmandu", "head office"], "is_relevant": True},
    {"query": "टेकसरुका कतिवटा शाखाहरु छन्?", "lang": "nepali", "keywords": ["seven branches", "7 branches"], "is_relevant": True},
    {"query": "के टेकसरुले पुरानो सेकेन्ड ह्यान्ड ल्यापटप किन्छ?", "lang": "nepali", "keywords": ["second-hand laptops", "buys", "inspection"], "is_relevant": True},
    {"query": "टेकसरुको मालिक को हुन्?", "lang": "nepali", "keywords": ["Nabin Nepali"], "is_relevant": True},
    {"query": "के टेकसरुले तेस्रो हात सामान बेच्छ?", "lang": "nepali", "keywords": ["third-hand"], "is_relevant": True},
    {"query": "भुक्तानी कसरी गर्न सकिन्छ?", "lang": "nepali", "keywords": ["cash", "payment", "bank transfer", "QR"], "is_relevant": True},
    {"query": "टेकसरुमा कुन कुन सामान पाइन्छ?", "lang": "nepali", "keywords": ["laptops", "smartphones", "accessories"], "is_relevant": True},
    {"query": "के सेकेन्ड ह्यान्ड ल्यापटपमा वारेन्टी पाइन्छ?", "lang": "nepali", "keywords": ["warranty", "second-hand"], "is_relevant": True},
    {"query": "मोबाइल र ल्यापटप मर्मत (repair) सेवा उपलब्ध छ?", "lang": "nepali", "keywords": ["repair", "devices"], "is_relevant": True},
    {"query": "नेपालभरि सामान डेलिभरी हुन कति समय लाग्छ?", "lang": "nepali", "keywords": ["delivery", "location"], "is_relevant": True},
    {"query": "के टेकसरुले भ्याट बिल (VAT invoice) दिन्छ?", "lang": "nepali", "keywords": ["VAT invoices"], "is_relevant": True},
    {"query": "सामान फिर्ता गर्ने वा साट्ने नीति के छ?", "lang": "nepali", "keywords": ["return", "refund", "exchange"], "is_relevant": True},
    {"query": "टेकसरुका लगानीकर्ताहरु को को हुन्?", "lang": "nepali", "keywords": ["Tek Bahadur Nepali", "investors", "stakeholders"], "is_relevant": True},
    {"query": "के टेकसरुले होम सर्भिस दिन्छ?", "lang": "nepali", "keywords": ["home service", "delivery"], "is_relevant": True},
    {"query": "मर्मत गर्दा मेरो डेटा सुरक्षित रहन्छ?", "lang": "nepali", "keywords": ["privacy", "data", "repair"], "is_relevant": True},
    {"query": "सम्पर्क नम्बर र इमेल के हो?", "lang": "nepali", "keywords": ["9829592158", "admin.haqdesk.ai@gmail.com"], "is_relevant": True},
    {"query": "डिभाइस हेल्थ स्कोर (device health score) भनेको के हो?", "lang": "nepali", "keywords": ["health score", "condition"], "is_relevant": True},
    {"query": "कम्पनीहरुको लागि थोक (bulk) खरिद सुविधा छ?", "lang": "nepali", "keywords": ["bulk", "corporate"], "is_relevant": True},
    {"query": "नयाँ ल्यापटपमा कति समयको वारेन्टी हुन्छ?", "lang": "nepali", "keywords": ["warranty"], "is_relevant": True},
    {"query": "गुनासो कसरी दर्ता गर्ने?", "lang": "nepali", "keywords": ["complaints", "support"], "is_relevant": True},

    # ================= ROMANIZED NEPALI IN-DOMAIN QUERIES (20 Queries) =================
    {"query": "techsuru ko head office kaha cha?", "lang": "romanized_nepali", "keywords": ["New Baneshwor", "Kathmandu", "head office"], "is_relevant": True},
    {"query": "techsuru le second hand laptop kincha ki kindaina?", "lang": "romanized_nepali", "keywords": ["second-hand laptops", "buys", "inspection"], "is_relevant": True},
    {"query": "kasto kasto payment method accept huncha?", "lang": "romanized_nepali", "keywords": ["cash", "payment", "bank transfer", "QR"], "is_relevant": True},
    {"query": "techsuru ko malik ko ho?", "lang": "romanized_nepali", "keywords": ["Nabin Nepali"], "is_relevant": True},
    {"query": "techsuru ko kati wota branch cha nepal ma?", "lang": "romanized_nepali", "keywords": ["seven branches", "7 branches"], "is_relevant": True},
    {"query": "k third hand saman pauxa techsuru ma?", "lang": "romanized_nepali", "keywords": ["third-hand"], "is_relevant": True},
    {"query": "second hand laptop ma warranty milxa?", "lang": "romanized_nepali", "keywords": ["warranty", "second-hand"], "is_relevant": True},
    {"query": "phone repair garna kati time lagxa?", "lang": "romanized_nepali", "keywords": ["repair", "same-day", "technician"], "is_relevant": True},
    {"query": "delivery charge kati parcha nepalko lagi?", "lang": "romanized_nepali", "keywords": ["delivery", "location"], "is_relevant": True},
    {"query": "vat bill milxa ki mildaina purchase ma?", "lang": "romanized_nepali", "keywords": ["VAT invoices"], "is_relevant": True},
    {"query": "techsuru ma purano phone exchange garna milcha?", "lang": "romanized_nepali", "keywords": ["exchange", "second-hand", "trade-in"], "is_relevant": True},
    {"query": "saman bigreko vaye firta garna milcha?", "lang": "romanized_nepali", "keywords": ["return", "refund", "exchange"], "is_relevant": True},
    {"query": "techsuru ko contact number k ho?", "lang": "romanized_nepali", "keywords": ["9829592158", "contact"], "is_relevant": True},
    {"query": "device health score vaneko k ho?", "lang": "romanized_nepali", "keywords": ["health score", "condition"], "is_relevant": True},
    {"query": "techsuru ma desktop accessories paunchha?", "lang": "romanized_nepali", "keywords": ["accessories", "laptops", "products"], "is_relevant": True},
    {"query": "corporate bulk order garna milcha?", "lang": "romanized_nepali", "keywords": ["bulk", "corporate"], "is_relevant": True},
    {"query": "repair gards data lost huncha कि safe rahanxa?", "lang": "romanized_nepali", "keywords": ["privacy", "data", "repair"], "is_relevant": True},
    {"query": "techsuru ko timing kasto cha open huneko?", "lang": "romanized_nepali", "keywords": ["hours", "open"], "is_relevant": True},
    {"query": "pokhara branch kaha निर cha?", "lang": "romanized_nepali", "keywords": ["Pokhara", "branches"], "is_relevant": True},
    {"query": "complaint register garne tarika k ho?", "lang": "romanized_nepali", "keywords": ["complaints", "escalation"], "is_relevant": True},

    # ================= OUT-OF-DOMAIN / IRRELEVANT QUERIES (17 Queries) =================
    {"query": "What is the capital city of France?", "lang": "english", "keywords": [], "is_relevant": False},
    {"query": "Do you deliver hot pepperoni pizza to my home?", "lang": "english", "keywords": [], "is_relevant": False},
    {"query": "What is the formula for calculating Einstein relativity E=mc2?", "lang": "english", "keywords": [], "is_relevant": False},
    {"query": "Can I book flight tickets to Pokhara through TechSuru?", "lang": "english", "keywords": [], "is_relevant": False},
    {"query": "Who won the FIFA World Cup football tournament in 2022?", "lang": "english", "keywords": [], "is_relevant": False},
    {"query": "How do I bake a chocolate cake at home?", "lang": "english", "keywords": [], "is_relevant": False},
    {"query": "Where can I buy fresh organic tomatoes in Kathmandu?", "lang": "english", "keywords": [], "is_relevant": False},
    {"query": "What is the weather forecast in Mustang tomorrow?", "lang": "english", "keywords": [], "is_relevant": False},
    {"query": "फ्रान्सको राजधानी सहर कुन हो?", "lang": "nepali", "keywords": [], "is_relevant": False},
    {"query": "आज काठमाडौंमा पानी पर्छ कि पर्दैन?", "lang": "nepali", "keywords": [], "is_relevant": False},
    {"query": "चिया कसरी मिठो बनाउने?", "lang": "nepali", "keywords": [], "is_relevant": False},
    {"query": "पोखरा जाने बसको टिकट पाइन्छ?", "lang": "nepali", "keywords": [], "is_relevant": False},
    {"query": "tapaile tapai ko ghar ma pizza order garna milcha?", "lang": "romanized_nepali", "keywords": [], "is_relevant": False},
    {"query": "today weather in kathmandu kasto cha?", "lang": "romanized_nepali", "keywords": [], "is_relevant": False},
    {"query": "bus ticket katna milcha pokhara ko lagi?", "lang": "romanized_nepali", "keywords": [], "is_relevant": False},
    {"query": "real madrid le match jityo ki jitenan?", "lang": "romanized_nepali", "keywords": [], "is_relevant": False},
    {"query": "nepal ko rastriya gaun kun ho?", "lang": "romanized_nepali", "keywords": [], "is_relevant": False}
]


def eval_query(query_str: str, business_id: int = 1, top_k: int = 3):
    """Retrieve top_k chunks for query using get_embedding_input() + Qdrant search."""
    search_text = get_embedding_input(query_str)
    embedding = rag_service.embedder.encode(f"query: {search_text}").tolist()

    from qdrant_client.models import Filter, FieldCondition, MatchValue
    query_filter = Filter(
        must=[FieldCondition(key="business_id", match=MatchValue(value=business_id))]
    )

    try:
        if hasattr(rag_service.qdrant, 'search'):
            results = rag_service.qdrant.search(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query_vector=embedding,
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
            )
        else:
            response = rag_service.qdrant.query_points(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query=embedding,
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
            )
            results = response.points

        return [{"score": r.score, "content": r.payload.get("content", "")} for r in results]
    except Exception as e:
        logger.error(f"Qdrant query error: {e}")
        return []


def run_full_evaluation():
    print("========================================================================")
    print("      HAQDESK AI EXPANDED RETRIEVAL & THRESHOLD EVALUATION (77 QUERIES)  ")
    print("========================================================================")

    in_domain_results = []
    out_domain_results = []

    lang_stats = {
        "english": {"top1": 0, "top3": 0, "total": 0},
        "nepali": {"top1": 0, "top3": 0, "total": 0},
        "romanized_nepali": {"top1": 0, "top3": 0, "total": 0}
    }

    for item in EXPANDED_EVAL_DATASET:
        res = eval_query(item["query"])
        top_score = res[0]["score"] if res else 0.0
        top_content = res[0]["content"] if res else ""

        if item["is_relevant"]:
            top1_hit = any(kw.lower() in top_content.lower() for kw in item["keywords"])
            top3_hit = any(
                any(kw.lower() in r["content"].lower() for kw in item["keywords"])
                for r in res
            )

            l = item["lang"]
            lang_stats[l]["total"] += 1
            if top1_hit:
                lang_stats[l]["top1"] += 1
            if top3_hit:
                lang_stats[l]["top3"] += 1

            in_domain_results.append({
                "query": item["query"],
                "lang": item["lang"],
                "score": top_score,
                "top1_hit": top1_hit,
                "matched_text": top_content[:80]
            })
        else:
            out_domain_results.append({
                "query": item["query"],
                "lang": item["lang"],
                "score": top_score,
                "matched_text": top_content[:80]
            })

    # Sort results by score
    in_domain_results.sort(key=lambda x: x["score"])
    out_domain_results.sort(key=lambda x: x["score"], reverse=True)

    print("\n--- 1. RETRIEVAL ACCURACY BY LANGUAGE ---")
    for l, s in lang_stats.items():
        top1_pct = (s["top1"] / s["total"] * 100) if s["total"] > 0 else 0
        top3_pct = (s["top3"] / s["total"] * 100) if s["total"] > 0 else 0
        print(f"  Language: {l:16s} | Top-1 Hit Rate: {top1_pct:6.1f}% ({s['top1']}/{s['total']}) | Top-3 Hit Rate: {top3_pct:6.1f}% ({s['top3']}/{s['total']})")

    # In-Domain Stats
    in_scores = [r["score"] for r in in_domain_results]
    out_scores = [r["score"] for r in out_domain_results]

    min_in = min(in_scores)
    max_in = max(in_scores)
    avg_in = statistics.mean(in_scores)
    std_in = statistics.stdev(in_scores)

    min_out = min(out_scores)
    max_out = max(out_scores)
    avg_out = statistics.mean(out_scores)
    std_out = statistics.stdev(out_scores)

    print("\n--- 2. SCORE RANGE & STATISTICAL OVERLAP ANALYSIS ---")
    print(f"  In-Domain (60 True Matches):")
    print(f"    Min: {min_in:.4f} | Max: {max_in:.4f} | Mean: {avg_in:.4f} | StdDev: {std_in:.4f}")
    print(f"  Out-of-Domain (17 False Positives):")
    print(f"    Min: {min_out:.4f} | Max: {max_out:.4f} | Mean: {avg_out:.4f} | StdDev: {std_out:.4f}")

    print("\n--- 3. OVERLAP ZONE DETAILED INSPECTION ---")
    print("Lowest 5 In-Domain Scores (True Matches):")
    for r in in_domain_results[:5]:
        print(f"  Score: {r['score']:.4f} | Lang: {r['lang']:16s} | Query: '{r['query']}' | Matched: {r['matched_text']}...")

    print("\nHighest 5 Out-of-Domain Scores (False Positives):")
    for r in out_domain_results[:5]:
        print(f"  Score: {r['score']:.4f} | Lang: {r['lang']:16s} | Query: '{r['query']}' | Matched: {r['matched_text']}...")

    # Threshold Option Analysis
    print("\n--- 4. PRODUCT TRADEOFF THRESHOLD OPTIONS ---")
    for t in [0.40, 0.42, 0.45, 0.48, 0.50]:
        fn_count = sum(1 for s in in_scores if s < t)
        fp_count = sum(1 for s in out_scores if s >= t)
        print(f"  Threshold {t:.2f} -> False Negatives (True matches rejected): {fn_count:2d}/{len(in_scores)} | False Positives (Irrelevant accepted): {fp_count:2d}/{len(out_scores)}")

    print("\n========================================================================")

if __name__ == "__main__":
    from app.core.config import settings
    run_full_evaluation()
