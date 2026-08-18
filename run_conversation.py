import json
import os
import argparse
from datetime import datetime
from characters import CHARACTERS
from stress_tests import STRESS_TESTS        
from mitigation import STRATEGIES
from llm_client import get_response
def _save_transcript(character_key, provider, model_name, strategy_name, character, transcript, partial=False):
    os.makedirs("logs", exist_ok=True)
    safe_model_name = model_name.replace("/", "-").replace(":", "-")
    suffix = "_PARTIAL" if partial else ""
    filename = os.path.join(
        "logs", f"{character_key}_{provider}_{safe_model_name}_{strategy_name}{suffix}.json"
    )
    result = {
        "character": character_key,
        "provider": provider,
        "model_name": model_name,
        "strategy": strategy_name,
        "timestamp": datetime.now().isoformat(),
        "key_facts": character["key_facts"],
        "transcript": transcript,
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    return filename
def run_roleplay(character_key, provider, model_name, strategy_name="none"):
    character = CHARACTERS[character_key]
    strategy_fn = STRATEGIES[strategy_name]
    stress_turns = STRESS_TESTS.get(character_key, [])
    if not stress_turns:
        from stress_tests import DEFAULT_STRESS_TURNS
        stress_turns = DEFAULT_STRESS_TURNS
    messages = []      
    transcript = []  
    for turn_index, turn in enumerate(stress_turns):
        user_msg = {"role": "user", "content": turn["text"]}
        messages.append(user_msg)
        messages = strategy_fn(character, messages, turn_index)
        try:
            try:
                reply = get_response(
                    provider=provider,
                    model_name=model_name,
                    system_prompt=character["system_prompt"],
                    messages=messages,
                )
            except Exception:
                print("First attempt failed, retrying once...")
                import time
                time.sleep(5)
                reply = get_response(
                    provider=provider,
                    model_name=model_name,
                    system_prompt=character["system_prompt"],
                    messages=messages,
                )
        except Exception as e:    
            partial_path = _save_transcript(
                character_key, provider, model_name, strategy_name, character, transcript, partial=True
            )
            print(f"\nAPI error after {len(transcript)} turn(s): {e}")
            print(f"Saved partial transcript to {partial_path} so this data isn't lost.")
            raise  
        import re
        clean_reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.DOTALL).strip()
        assistant_msg = {"role": "assistant", "content": clean_reply}
        messages.append(assistant_msg)
        transcript.append({
            "turn_index": turn_index,
            "category": turn["category"],
            "user_text": turn["text"],
            "assistant_text": clean_reply,
        })
        print(f"[{turn_index}] ({turn['category']}) USER: {turn['text']}")
        print(f"      {character['name']}: {reply}\n")
        _save_transcript(character_key, provider, model_name, strategy_name, character, transcript)
    filename = _save_transcript(character_key, provider, model_name, strategy_name, character, transcript)
    print(f"\nSaved transcript to {filename}")
    return filename
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a persona-consistency roleplay conversation.")
    parser.add_argument("--character", default="grom_blacksmith", choices=CHARACTERS.keys())
    parser.add_argument("--provider", default="groq", choices=["groq", "google", "openrouter", "github", "ollama"])
    parser.add_argument("--model", default="llama-3.3-70b-versatile")
    parser.add_argument("--strategy", default="none", choices=STRATEGIES.keys())
    args = parser.parse_args()
    run_roleplay(args.character, args.provider, args.model, args.strategy)