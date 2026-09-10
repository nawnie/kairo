"""Command-line question interface for a supplied program path."""
import argparse
import json
import sys

from .question_path import Questioner


DEFAULT_PROTOCOL = {
    "initial_suffix_depth": 1, "query_budget": 2000, "symbol_budget": 20000,
    "seed": 24123, "middle_depth": 2, "max_middle_depth": 2,
    "random_probes": 80, "random_max_length": 8, "round_budget": 20,
}


def main():
    parser = argparse.ArgumentParser(description="Ask Kairo a question about a supplied program path.")
    parser.add_argument("program_path")
    parser.add_argument("question", nargs="?")
    parser.add_argument("--interactive", action="store_true", help="read one question per stdin line")
    args = parser.parse_args()
    questioner = Questioner(args.program_path, DEFAULT_PROTOCOL)
    if args.interactive:
        for line in sys.stdin:
            question = line.strip()
            if question:
                print(json.dumps(questioner.ask(question)), flush=True)
    elif args.question:
        print(json.dumps(questioner.ask(args.question), indent=2))
    else:
        parser.error("question is required unless --interactive is used")


if __name__ == "__main__":
    main()
