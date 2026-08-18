
import json
import glob
import csv
import os
import matplotlib.pyplot as plt
STRATEGY_COLORS = {
    "none": "#4C72B0",             
    "periodic_reminder": "#DD8452", 
}
def load_all_scored(results_dir="results"):
    files = glob.glob(f"{results_dir}/*_scored.json")
    all_results = []
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            all_results.append(json.load(f))
    return all_results
def summarize(all_results, out_csv="results/summary.csv"):
    rows = []
    for r in all_results:
        total_contradictions = sum(t["num_contradictions"] for t in r["per_turn"])
        num_turns = len(r["per_turn"])
        rows.append({
            "character": r["character"],
            "provider": r["provider"],
            "model_name": r["model_name"],
            "strategy": r["strategy"],
            "total_contradictions": total_contradictions,
            "num_turns": num_turns,
            "avg_contradiction_rate": round(total_contradictions / num_turns, 3) if num_turns else 0,
        })
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved summary table to {out_csv}\n")
    for row in rows:
        print(row)
    return rows
def _short_model_name(model_name):
    name = model_name.split("/")[-1]  
    name = name.replace(":free", "")
    return name
def _group_by_character(all_results):
    by_char = {}
    for r in all_results:
        by_char.setdefault(r["character"], []).append(r)
    return by_char
def _plot_bar_grouped(ax, rows, title):
    models = sorted(set(r["model_name"] for r in rows), key=_short_model_name)
    strategies = sorted(set(r["strategy"] for r in rows))
    n_strategies = len(strategies)
    bar_width = 0.8 / max(n_strategies, 1)
    x_positions = range(len(models))
    for i, strategy in enumerate(strategies):
        values = []
        for model in models:
            match = [r for r in rows if r["model_name"] == model and r["strategy"] == strategy]
            values.append(match[0]["avg_contradiction_rate"] if match else 0)
        offsets = [x + i * bar_width - (bar_width * (n_strategies - 1) / 2) for x in x_positions]
        bars = ax.bar(
            offsets, values, width=bar_width,
            label=strategy, color=STRATEGY_COLORS.get(strategy, "#999999"),
        ) 
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.03,
                    f"{value:.2f}", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(list(x_positions))
    ax.set_xticklabels([_short_model_name(m) for m in models], fontsize=9)
    ax.set_ylabel("Avg. contradictions per turn")
    ax.set_title(title, fontsize=11)
    ax.legend(fontsize=8)
def plot_bar_per_character(rows, out_dir="results"):
    by_char = _group_by_character(rows)
    saved = []
    for character, char_rows in by_char.items():
        fig, ax = plt.subplots(figsize=(6, 5))
        _plot_bar_grouped(ax, char_rows, title=f"{character}: model x strategy comparison")
        plt.tight_layout()
        out_path = os.path.join(out_dir, f"bar_{character}.png")
        plt.savefig(out_path)
        plt.close(fig)
        saved.append(out_path)
        print(f"Saved {out_path}")
    return saved
def plot_bar_combined(rows, out_path="results/bar_combined.png"):
    by_char = _group_by_character(rows)
    characters = sorted(by_char.keys())
    n = len(characters)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 5), sharey=True)
    if n == 1:
        axes = [axes]
    for ax, character in zip(axes, characters):
        _plot_bar_grouped(ax, by_char[character], title=character)
    fig.suptitle("Persona-consistency comparison across all characters", fontsize=13)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close(fig)
    print(f"Saved {out_path}")
def _plot_drift_lines(ax, rows, title):
    for r in rows:
        label = f"{_short_model_name(r['model_name'])} | {r['strategy']}"
        windows = r["drift_by_window"]
        x = [w["window_start"] for w in windows]
        y = [w["contradiction_rate"] for w in windows]
        color = STRATEGY_COLORS.get(r["strategy"], "#999999")
        models = sorted(set(rr["model_name"] for rr in rows), key=_short_model_name)
        linestyle = "-" if r["model_name"] == models[0] else "--"
        ax.plot(x, y, marker="o", label=label, color=color, linestyle=linestyle)
    ax.set_xlabel("Conversation turn (window start)")
    ax.set_ylabel("Contradiction rate")
    ax.set_title(title, fontsize=11)
    ax.legend(fontsize=8)
def plot_drift_per_character(all_results, out_dir="results"):
    by_char = _group_by_character(all_results)
    saved = []
    for character, rows in by_char.items():
        fig, ax = plt.subplots(figsize=(7, 5))
        _plot_drift_lines(ax, rows, title=f"{character}: persona drift over time")
        plt.tight_layout()
        out_path = os.path.join(out_dir, f"drift_{character}.png")
        plt.savefig(out_path)
        plt.close(fig)
        saved.append(out_path)
        print(f"Saved {out_path}")
    return saved
def plot_drift_combined(all_results, out_path="results/drift_combined.png"):
    by_char = _group_by_character(all_results)
    characters = sorted(by_char.keys())
    n = len(characters)
    fig, axes = plt.subplots(1, n, figsize=(6 * n, 5), sharey=True)
    if n == 1:
        axes = [axes]
    for ax, character in zip(axes, characters):
        _plot_drift_lines(ax, by_char[character], title=character)
    fig.suptitle("Persona drift over conversation length, by character", fontsize=13)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close(fig)
    print(f"Saved {out_path}")
if __name__ == "__main__":
    all_results = load_all_scored()
    if not all_results:
        print("No scored results found in results/. Run consistency_check.py first.")
    else:
        rows = summarize(all_results)
        os.makedirs("results", exist_ok=True)
        plot_bar_per_character(rows)
        plot_bar_combined(rows)
        plot_drift_per_character(all_results)
        plot_drift_combined(all_results)