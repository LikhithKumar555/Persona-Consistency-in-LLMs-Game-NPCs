
import json
from transformers import pipeline
_nli_pipeline = None
def _get_nli_pipeline():
    global _nli_pipeline
    if _nli_pipeline is None: 
        _nli_pipeline = pipeline("text-classification", model="facebook/bart-large-mnli")
    return _nli_pipeline
import re
def normalize_statement(statement, character_name):
    replacements = [
        (r"\bI'm\b", f"{character_name} is"),
        (r"\bI am\b", f"{character_name} is"),
        (r"\bI've\b", f"{character_name} has"),
        (r"\bI have\b", f"{character_name} has"),
        (r"\bmy\b", f"{character_name}'s"),
        (r"\bMy\b", f"{character_name}'s"),
        (r"\bI\b", character_name),
        (r"\bme\b", character_name),
    ]
    result = statement
    for pattern, repl in replacements:
        result = re.sub(pattern, repl, result)
    return result
def check_contradiction(fact, statement, character_name=None):
    if character_name:
        statement = normalize_statement(statement, character_name)
    nli = _get_nli_pipeline()
    results = nli(fact, text_pair=statement, top_k=None)
    scores = {r["label"].lower(): r["score"] for r in results}
    contradiction_score = scores.get("contradiction", 0.0)
    top_label = max(scores, key=scores.get)
    return {"label": top_label, "score": contradiction_score, "all_scores": scores}
def score_transcript(transcript_path, window_size=5):
    with open(transcript_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    key_facts = data["key_facts"]
    character_name = data["character"].split("_")[0].capitalize()  # e.g. "grom_blacksmith" -> "Grom"
    per_turn = []
    for turn in data["transcript"]:
        statement = turn["assistant_text"]
        contradictions = 0
        worst_score = 0.0
        for fact in key_facts:
            result = check_contradiction(fact, statement, character_name=character_name)
            if result["score"] > 0.5:
                contradictions += 1
                worst_score = max(worst_score, result["score"])
        per_turn.append({
            "turn_index": turn["turn_index"],
            "category": turn["category"],
            "num_contradictions": contradictions,
            "worst_score": worst_score,
        })
        print(f"Turn {turn['turn_index']} ({turn['category']}): "
              f"{contradictions} contradiction(s), worst score={worst_score:.2f}")
    drift_by_window = []
    for start in range(0, len(per_turn), window_size):
        window = per_turn[start:start + window_size]
        total_contradictions = sum(t["num_contradictions"] for t in window)
        rate = total_contradictions / len(window) if window else 0
        drift_by_window.append({
            "window_start": start,
            "window_end": start + len(window) - 1,
            "contradiction_rate": rate,
        })
    return {
        "source_file": transcript_path,
        "character": data["character"],
        "provider": data["provider"],
        "model_name": data["model_name"],
        "strategy": data["strategy"],
        "per_turn": per_turn,
        "drift_by_window": drift_by_window,
    }
if __name__ == "__main__":
    import argparse
    import os
    parser = argparse.ArgumentParser(description="Score a transcript for persona-consistency drift.")
    parser.add_argument("--transcript", required=True, help="Path to a transcript JSON file")
    args = parser.parse_args()
    result = score_transcript(args.transcript)
    os.makedirs("results", exist_ok=True)
    out_name = "results/" + os.path.basename(args.transcript).replace(".json", "_scored.json")
    with open(out_name, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nSaved scored results to {out_name}")
