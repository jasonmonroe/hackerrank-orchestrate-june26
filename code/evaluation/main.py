# code/evaluation/main.py

# Python Libraries
import inspect
from time import sleep
import openai

# Local Libraries
from evaluation.claim_analyzer import ClaimAnalyzer
from evaluation.claim_handler import ClaimHandler

from src.constants import (
    CSV_HEADERS,
    MODEL_NAME,
    PAUSE_TIMER,
    REPORT_FILE,
    SAMPLE_CLAIMS_FILE,
    SLEEP_TIMER,
    TOKEN_UNIT, SLEEP_TIMER_INC,
)
from src.data_handler import DataHandler
from src.image_handler import ImageHandler
from src.utils import show_banner, start_timer

def run_claim_pipeline(data_handle: DataHandler, image_handle: ImageHandler) -> None:

    # Extract the actual damage claim from the conversation
    analyzer = ClaimAnalyzer(data_handle, image_handle)
    claim = ClaimHandler()

    # For each row in `claims.csv`, generate one row in `output.csv`
    csv_rows = [list(CSV_HEADERS)]
    csv_row_cnt = len(analyzer.data.claims)

    # Analyze each claim from the dataset case by case
    extra_time = 0
    for idx, row in enumerate(analyzer.data.claims.itertuples()):
        print(f"\n# --- Claim analysis for row {idx + 1} of {csv_row_cnt} begins --- #")

        while True:
            try:
                # Analyzing claim and get final dataset.
                final_dataset = analyzer.analyze_claim(idx, "Basic Prompt")
                break # Success! Break the retry loop and move forward

            except openai.RateLimitError as e:
                print(f"{e}")
                print(f"\n⚠️ Hit Token Quota Limit! Pausing pipeline for {SLEEP_TIMER} seconds for another attempt...")
                sleep(SLEEP_TIMER)
                extra_time += SLEEP_TIMER_INC
                print(f"🔄 Adding extra time ({extra_time}).  Resuming analysis...")

        # Create CSV data
        claim.update(final_dataset)
        csv_rows.append(claim.export_csv_row())

        # Consistent pacing between normal loops
        print(claim.progress(idx, csv_row_cnt))
        sleep(PAUSE_TIMER + extra_time)

    # Write the output to a file
    claim.write_output(csv_rows)


def run_evaluation_report_pipeline(data_handle: DataHandler, image_handle: ImageHandler) -> None:
    """
    You write a script (usually in code/evaluation/main.py) that loops through sample_claims.csv, compares your model's
    predictions to the expected_output columns, and calculates your accuracy. This script should also track how many
    tokens you use and how long each call takes.

    :param data_handle:
    :param image_handle:
    :return:
    """

    print("# --- Evaluation Workflow Start --- #")

    show_banner(
        "Evaluation Report".upper(), [
            f"Evaluating model performance on {SAMPLE_CLAIMS_FILE}.",
            "Evaluating Strategies: `Basic` and `Chain-of-Thought` Prompts"
        ],
        center_subtitle_text=True
    )

    # Explicitly load the evaluation answer key sample dataset
    data_handle.load_data({"sample": True})
    sample_data = data_handle.claims
    sample_data_len = len(sample_data)

    results = {}
    strategies = ["Basic Prompt", "Chain-of-Thought Prompt"]

    for strategy in strategies:

        analyzer = ClaimAnalyzer(data_handle, image_handle)

        metrics = {
            "correct": 0,
            "total": sample_data_len,
            "total_tokens": 0,
            "total_cost": 0.0,
            "start_time": start_timer()
        }

        for idx in range(sample_data_len):
            # Pass the dynamic loop strategy directly to your analyzer!
            print(f"\n# --- Evaluating {strategy} - Row {idx + 1} of {sample_data_len} --- #")

            response = analyzer.analyze_claim(idx, strategy=strategy)

            # Ensure 'expected_claim_status' is your actual CSV ground truth column
            ground_truth = sample_data.iloc[idx].get("expected_claim_status", sample_data.iloc[idx]["claim_status"])

            if response["claim_status"] == ground_truth:
                metrics["correct"] += 1

            # Metric accounting remains standard
            metrics["total_tokens"] += response.get("usage", {}).get("total_tokens", 0)
            metrics["total_cost"] = (metrics["total_tokens"] / TOKEN_UNIT) * 0.01

        metrics["duration"] = start_timer() - metrics["start_time"]
        metrics["accuracy"] = (metrics["correct"] / metrics["total"]) * 100 if metrics["total"] > 0 else 0
        results[strategy] = metrics

    subtitles = []
    for strategy, metric in results.items():
        subtitles.append(f"Strategy: {strategy}")
        subtitles.append(f"🎯️Accuracy: {metric['accuracy']:.2f}%")
        subtitles.append(f"ℹ️Total Time: {metric['duration']:.2f}s")
        subtitles.append(f"ℹ️Tokens: {metric['total_tokens']}")
        subtitles.append(f"💰️Est Cost: ${metric['total_cost']:.2f}\n")

    show_banner("Evaluation Report".upper(), subtitles)

    print("# --- Evaluation Workflow Complete --- #")

    # Now it's time to generate a report template to be used.
    generate_report_template(results)

def generate_report_template(results: dict) -> None:
    """
    Generates a report template that will be outputted to a Markdown file.
    :param results:
    :return:
    """

    print("# --- Generating Report Template --- #")

    strategy_rows = []
    total_tokens_sum = 0
    total_cost_sum = 0.0

    for strategy, metrics in results.items():
        strategy_rows.append(
            f"| {strategy} | {metrics['accuracy']:.2f}% | {metrics['duration']:.2f}s | ${metrics['total_cost']:.2f} |"
        )
        total_tokens_sum += metrics['total_tokens']
        total_cost_sum += metrics['total_cost']

    strategy_comparison_table = "\n".join(strategy_rows)

    # Wrap the multi-line string in inspect.cleandoc to drop layout tabs/spaces
    content = inspect.cleandoc(f"""
        # Operational Evaluation Report
        
        ### Strategy Comparison
        | Strategy | Accuracy | Latency (avg) | Cost (est) |
        | :--- | :--- | :--- | :--- |
        {strategy_comparison_table}
        
        ## Operational Analysis
        - **Model Used:** {MODEL_NAME}
        - **Total Token Usage:** {total_tokens_sum:,}
        - **Approximate Cost:** ${total_cost_sum:.2f}
        - **TPM/RPM Observations:**
        
        ## Final Strategy Choice
        We chose Strategy [X] because...
    """).strip()

    with open(REPORT_FILE, "w") as f:
        f.write(content)
