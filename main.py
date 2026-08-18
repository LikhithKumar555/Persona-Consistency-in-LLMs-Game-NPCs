
from characters import CHARACTERS
from mitigation import STRATEGIES
from run_conversation import run_roleplay
from consistency_check import score_transcript
import json
import os
CHARACTERS_TO_RUN = ["grom_blacksmith", "lyra_healer", "vex_merchant"]  
STRATEGIES_TO_RUN = ["none", "periodic_reminder"]  
MODELS_TO_RUN = [
    ("ollama", "llama3.2:3b"),
    ("ollama", "mistral:7b"),
    ("ollama", "phi3:3.8b"),
]
def run_full_experiment():
    transcript_paths = []
    for character_key in CHARACTERS_TO_RUN:
        for provider, model_name in MODELS_TO_RUN:
            for strategy_name in STRATEGIES_TO_RUN:
                safe_model_name = model_name.replace("/", "-").replace(":", "-")
                expected_path = os.path.join(
                    "logs", f"{character_key}_{provider}_{safe_model_name}_{strategy_name}.json"
                )
                if os.path.exists(expected_path):
                    print(f"\nSkipping {character_key} | {provider}/{model_name} | {strategy_name} "
                          f"(already exists at {expected_path})")
                    transcript_paths.append(expected_path)
                    continue
                print(f"\n=== Running {character_key} | {provider}/{model_name} | {strategy_name} ===\n")
                path = run_roleplay(character_key, provider, model_name, strategy_name)
                transcript_paths.append(path)
    os.makedirs("results", exist_ok=True)
    for path in transcript_paths:
        print(f"\n=== Scoring {path} ===\n")
        result = score_transcript(path)
        out_name = "results/" + os.path.basename(path).replace(".json", "_scored.json")
        with open(out_name, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    print("\nAll runs complete. Now run: python analyze_results.py")
if __name__ == "__main__":
    run_full_experiment()
