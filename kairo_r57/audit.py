import json
from pathlib import Path


def main():
    value = json.loads(Path("verification/R57_R0.json").read_text()); rows = value["rows"]
    assert len(rows) == value["case_count"] == 25
    assert all(row["r0_mae"] == row["reload_mae"] for row in rows)
    assert all(row["peak_python_bytes"] > 0 and row["elapsed_seconds"] >= 0 for row in rows)
    print(json.dumps({"audit": "R57-R0", "rows": len(rows), "reload_exact": True, "resource_receipts": True}))


if __name__ == "__main__":
    main()
