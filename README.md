# Persona Consistency in LLM-Driven Game NPCs

This project is about checking if AI language model can staying in character for long conversation, when we use it as NPC in game, or it just start contradicting itself after some time. Also checking if some simple trick can fix this problem or not.

## What this project do

- Giving LLM a game character persona (system prompt plus list of key facts about the character)
- Running it through fix 15 turn stress test conversation (normal chat, contradiction bait question, off topic question, and question that trying to break the character directly)
- Checking every reply against the character key facts, using pretrained NLI model (facebook/bart-large-mnli) for detecting contradiction
- Tracking the contradiction rate in window of 5 turns, so can see how drift building up over the conversation
- Comparing two strategy: no help at all (none), vs periodically reminding model about its own persona facts every 4 turn
- Running all this across 3 character and 3 local model using Ollama, then plotting the result

## Characters I tested

| Character | Condition |
|---|---|
| Grom (blacksmith) | minimal backstory (this is base line) |
| Lyra (healer) | detailed backstory |
| Vex (merchant) | told to show strong emotion |

## Models I tested

All running local through Ollama, so no API cost and no rate limit problem:
- llama3.2:3b
- mistral:7b
- phi3:3.8b

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Install [Ollama](https://ollama.com) and pull the models like this:
```bash
ollama pull llama3.2:3b
ollama pull mistral:7b
ollama pull phi3:3.8b
```

## How to use

For run one single conversation:
```bash
python run_conversation.py --character grom_blacksmith --provider ollama --model llama3.2:3b --strategy none
```

For checking it for contradiction after:
```bash
python consistency_check.py --transcript logs/grom_blacksmith_ollama_llama3.2-3b_none.json
```

For run the whole experiment grid (all character x model x strategy together) and also making all the plot:
```bash
python main.py
python analyze_results.py
```

All result (csv file and the charts) will save inside `results/` folder.

## Project files

```
characters.py          # persona for each character (system prompt + key facts)
stress_tests.py         # the 15 question set for each character
mitigation.py            # the "none" and "periodic_reminder" strategy
llm_client.py             # client wrapper for calling Ollama
run_conversation.py        # run one roleplay conversation and save the transcript
consistency_check.py        # check contradiction using NLI model
analyze_results.py           # make summary csv and the charts
main.py                       # run everything together, full grid
logs/                           # saved conversation transcript
results/                         # scored result, summary.csv, and plots
```

## What I found

- **Backstory detail matter the most.** Character with detailed backstory (Lyra) had almost zero contradiction in most model, but character with minimal backstory (Grom) had the most contradiction, going up to 1.8 per turn.
- **Reminder strategy not always helpful.** It clearly helping the bigger model (mistral:7b), but for smallest model (phi3:3.8b) it actually made thing worse for two of the three character.

Full explanation and analysis is in the  Report.pdf.
