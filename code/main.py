# code/main.py

# +-----------------------------------+
# | HACKERRANK ORCHESTRATE CHALLENGE  |
# +-----------------------------------+
# @link https://www.hackerrank.com/contests/hackerrank-orchestrate-june26/challenges/multi-modal-review
# Clone Repo - @link https://github.com/interviewstreet/hackerrank-orchestrate-june26

__author__ = "Jason Monroe (jason@jasonmonroe.com)"
__copyright__ = "Copyright © 2011-2026 Monroe Labs"
__date__ = "2026-07-08"
__version__ = "1.0.0"

# Python Libraries
from dotenv import load_dotenv
load_dotenv("../.env")

import sys
import warnings

# Local Libraries
from evaluation.main import run_claim_pipeline, run_evaluation_report_pipeline
from src.data_handler import DataHandler
from src.image_handler import ImageHandler
from src.utils import start_timer, show_timer, show_banner


def run_main_pipeline(args: dict):
    subtitles = ["The Insurance Agent Adjuster at your service!"]
    for key, value in args.items():
        icon = "✅" if value else "❌"
        subtitles.append(f"Args: {key.title().replace('_', ' ').lower()}: {icon} ")

    show_banner("HackerRank Orchestrate".upper(), subtitles)

    # Process data
    data_handle = DataHandler()
    data_handle.load_data(args)
    image_handle = ImageHandler(args.get("eda", False))

    if args.get("eda"):
        data_handle.describe()

    run_claim_pipeline(data_handle, image_handle)

    # Run evaluation pipeline
    if args.get("eval"):
        run_evaluation_report_pipeline(data_handle, image_handle)


def parse_args(command_line_args: list[str]) -> dict:
    args_list = ["--eda", "--eval", "--sample"]
    return {arg.strip('--'): (arg in command_line_args) for arg in args_list}


if __name__ == "__main__":
    warnings.filterwarnings('ignore')

    prog_start_time = start_timer()
    run_id = str(int(prog_start_time))[-6:]
    print(f'\n----- 🖨️️ START RUN ID: {run_id} 🖨️️ -----')

    args = parse_args(sys.argv[1:])
    run_main_pipeline(args)

    show_timer(prog_start_time)
    print(f'\n----- 🖨️️ END RUN ID: {run_id} 🖨️️ -----\n')
