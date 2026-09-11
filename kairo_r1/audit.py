import json
from pathlib import Path


def main():
    value = json.loads(Path("verification/R58_R1.json").read_text()); rows = value["rows"]
    assert len(rows) == value["case_count"] == 30
    assert all(row["reservoir_mae"] == row["reload_mae"] for row in rows)
    assert all(row["peak_python_bytes"] > 0 and row["peak_rss_bytes"] > 0 and row["elapsed_seconds"] >= 0 for row in rows)
    print(json.dumps({"audit": "R58-R1", "rows": len(rows), "reload_exact": True, "resource_receipts": True, "peak_rss": True}))


if __name__ == "__main__": main()
