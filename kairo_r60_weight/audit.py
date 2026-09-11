import json
from pathlib import Path


def main():
    value = json.loads(Path("verification/R60_R0_WEIGHT.json").read_text()); assert value["case_count"] == 125; assert len(value["mean_mae_by_weight"]) == 5
    print(json.dumps({"audit": "R60-R0-weight-sweep", "rows": value["case_count"], "weights": sorted(value["mean_mae_by_weight"]), "best_weight": value["best_weight"]}))


if __name__ == "__main__": main()
