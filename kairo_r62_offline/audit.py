import json
from kairo_r62_offline.experiment import run


def main():
    value = run(); assert len(value["rows"]) == 9; assert all(row["mismatch_count"] >= 0 for row in value["rows"])
    print(json.dumps({"audit": "R62-R0-offline-context", "rows": len(value["rows"]), "prechallenge_only": True, "goal_achieved": False}))


if __name__ == "__main__": main()
