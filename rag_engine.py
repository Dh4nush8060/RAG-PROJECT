"""RAG retrieval engine combining vector search with contextual prompting."""
import json
from embedding_engine import query_similar, embed_document, chunk_text


def build_rag_context(report_data, patient_id=None, query=None):
    """Build RAG context from report data and vector search."""

    context_parts = []

    # 1. Include the structured report data
    if report_data.get("test_results"):
        context_parts.append("=== PATIENT LAB RESULTS ===")
        for test in report_data["test_results"]:
            status_emoji = "✅" if test["status"] == "Normal" else ("⚠️" if test["status"] == "High" else "🔻")
            ref_range = f"(Ref: {test['ref_low']}-{test['ref_high']})" if test.get("ref_low") is not None else ""
            context_parts.append(
                f"{status_emoji} {test['name']}: {test['value']} {test['unit']} {ref_range} [{test['status']}]"
            )

    # 2. Retrieve relevant context from vector DB
    if query:
        search_query = query
    elif report_data.get("test_results"):
        # Build a query from abnormal results
        abnormal = [t for t in report_data["test_results"] if t["status"] != "Normal"]
        if abnormal:
            search_query = "Medical explanation for: " + ", ".join(
                [f"{t['name']} is {t['status']} at {t['value']} {t['unit']}" for t in abnormal[:5]]
            )
        else:
            search_query = "Complete blood count and biochemistry normal results health advice"
    else:
        search_query = report_data.get("raw_text", "")[:200]

    similar_docs = query_similar(search_query, patient_id=patient_id, n_results=3)
    if similar_docs:
        context_parts.append("\n=== RELATED CLINICAL CONTEXT ===")
        for doc in similar_docs:
            context_parts.append(doc["text"])

    return "\n".join(context_parts)


def embed_report(report_id, patient_id, report_data):
    """Embed a parsed report into the vector database."""
    texts_to_embed = []

    # Embed raw text
    if report_data.get("raw_text"):
        chunks = chunk_text(report_data["raw_text"])
        texts_to_embed.extend(chunks)

    # Embed structured results as text
    if report_data.get("test_results"):
        for test in report_data["test_results"]:
            test_text = (
                f"Test: {test['name']}, Value: {test['value']} {test['unit']}, "
                f"Reference Range: {test.get('ref_low', 'N/A')}-{test.get('ref_high', 'N/A')}, "
                f"Status: {test['status']}, Category: {test.get('category', 'General')}"
            )
            texts_to_embed.append(test_text)

    if texts_to_embed:
        return embed_document(report_id, patient_id, texts_to_embed)
    return 0
