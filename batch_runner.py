import sys
import os
import json
import csv
import time
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from pipeline import TriagePipeline

console = Console()

def load_dataset(file_path: str) -> list:
    """Supports .txt (one message per line), .json, and .csv formats."""
    messages = []
    
    if file_path.endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as f:
            messages = [line.strip() for line in f if line.strip()]
            
    elif file_path.endswith('.json'):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                if data and isinstance(data[0], dict):
                    # Find the text/message key
                    key = next((k for k in ['message', 'text', 'body', 'input', 'content'] if k in data[0]), list(data[0].keys())[0])
                    messages = [item[key] for item in data if key in item]
                else:
                    messages = [str(item) for item in data]
                    
    elif file_path.endswith('.csv'):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                key = next((k for k in ['message', 'text', 'body', 'input', 'content'] if k.lower() in [fn.lower() for fn in reader.fieldnames]), reader.fieldnames[0])
                messages = [row[key] for row in reader if row.get(key)]
            else:
                f.seek(0)
                messages = [row[0] for row in csv.reader(f) if row]
                
    return messages


def process_dataset(file_path: str):
    if not os.path.exists(file_path):
        console.print(f"[bold red]Error:[/bold red] File '{file_path}' not found.")
        return

    messages = load_dataset(file_path)
    console.print(f"\n[bold green]✓ Loaded {len(messages)} messages from {file_path}[/bold green]\n")

    pipeline = TriagePipeline()
    results = []
    
    table = Table(title=f"Autonomous Triage Stream — {os.path.basename(file_path)}", show_lines=True)
    table.add_column("#", justify="center", width=4)
    table.add_column("Message Preview", style="cyan", width=30)
    table.add_column("Category", style="magenta", width=18)
    table.add_column("Pri", justify="center", width=6)
    table.add_column("Human", justify="center", width=7)
    table.add_column("Conf", justify="right", width=6)
    table.add_column("Summary / Suggested Action", style="green")

    start_total = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[yellow]Triaging messages...", total=len(messages))

        for idx, msg in enumerate(messages, 1):
            decision = pipeline.run(msg)
            results.append({
                "id": idx,
                "input_message": msg,
                **decision
            })

            # Formatting styles
            p_color = "bold red" if decision["priority"] in ["P0", "P1"] else "yellow"
            h_badge = "[bold red]YES[/bold red]" if decision["needs_human"] else "[green]NO[/green]"
            
            # Formatting styles
            p_color = "bold red" if decision["priority"] in ["P0", "P1"] else "yellow"
            h_badge = "[bold red]YES[/bold red]" if decision["needs_human"] else "[green]NO[/green]"
            
            # Create a visible badge if tools were used (Emoji removed)
            tool_badge = f"\n[bold cyan]Tools Used: {decision['tools_triggered']}[/bold cyan]" if decision.get("tools_triggered", "None") != "None" else ""

            table.add_row(
                str(idx),
                msg[:28] + "..." if len(msg) > 30 else msg,
                decision["category"],
                f"[{p_color}]{decision['priority']}[/{p_color}]",
                h_badge,
                f"{decision['confidence']}%",
                f"{decision['summary']}{tool_badge}\n[italic dim]Action: {decision['suggested_action']}[/italic dim]"
            )
            progress.advance(task)

    console.print(table)

    total_time = time.time() - start_total
    avg_latency = total_time / max(len(messages), 1)

    # Save outputs
    with open("triage_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    with open("triage_results.csv", "w", newline="", encoding="utf-8") as f:
        # We added "tools_triggered" to this list!
        writer = csv.DictWriter(f, fieldnames=["id", "input_message", "category", "priority", "summary", "suggested_action", "needs_human", "confidence", "tools_triggered"])
        writer.writeheader()
        writer.writerows(results)

    # Summary Stats
    p0_count = sum(1 for r in results if r["priority"] == "P0")
    p1_count = sum(1 for r in results if r["priority"] == "P1")
    human_count = sum(1 for r in results if r["needs_human"])

    console.print(f"\n[bold]========== BATCH RUN METRICS ==========[/bold]")
    console.print(f"Total Processed   : [bold cyan]{len(messages)} messages[/bold cyan]")
    console.print(f"Total Time        : [bold cyan]{total_time:.2f}s[/bold cyan] (~{avg_latency:.2f}s/message)")
    console.print(f"Escalated to Human: [bold yellow]{human_count}/{len(messages)} ({human_count/len(messages)*100:.1f}%)[/bold yellow]")
    console.print(f"High-Urgency (P0/P1): [bold red]{p0_count + p1_count}[/bold red] (P0: {p0_count}, P1: {p1_count})")
    console.print(f"Saved artifacts   : [bold green]triage_results.json[/bold green] & [bold green]triage_results.csv[/bold green]")
    console.print(f"[bold]========================================[/bold]\n")

if __name__ == "__main__":
    file_arg = sys.argv[1] if len(sys.argv) > 1 else "messages.txt"
    process_dataset(file_arg)