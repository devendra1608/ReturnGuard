
import argparse
import csv
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "synthetic_returns.csv"

SCENARIOS = [
    "legitimate_return",
    "outside_return_window",
    "duplicate_request",
    "suspicious_behavior",
    "missing_evidence",
    "high_value_return",
    "contradictory_evidence",
]


def generate_case(case_number: int, rng: random.Random) -> dict:
    """Generate one reproducible synthetic return request."""

    scenario = SCENARIOS[(case_number - 1) % len(SCENARIOS)]

    # Start with an ordinary return request.
    case = {
        "case_id": f"RET-{case_number:06d}",
        "order_id": f"ORD-{case_number:06d}",
        "customer_id": f"CUS-{rng.randint(1, 200):04d}",
        "order_amount": round(rng.uniform(100, 5000), 2),
        "refund_amount": 0.0,
        "days_since_delivery": rng.randint(1, 25),
        "return_reason": "changed_mind",
        "evidence_available": True,
        "previous_returns_90d": rng.randint(0, 3),
        "duplicate_request": False,
        "scenario_type": scenario,
        "risk_label": "legitimate",
        "policy_eligible": True,
        "expected_outcome": "auto_approve",
    }

    case["refund_amount"] = case["order_amount"]

    if scenario == "legitimate_return":
        case["return_reason"] = "changed_mind"

    elif scenario == "outside_return_window":
        case["days_since_delivery"] = rng.randint(31, 60)
        case["policy_eligible"] = False
        case["expected_outcome"] = "human_review"

    elif scenario == "duplicate_request":
        case["duplicate_request"] = True
        case["risk_label"] = "suspicious"
        case["expected_outcome"] = "human_review"

    elif scenario == "suspicious_behavior":
        case["previous_returns_90d"] = rng.randint(8, 15)
        case["risk_label"] = "suspicious"
        case["expected_outcome"] = "human_review"

    elif scenario == "missing_evidence":
        case["return_reason"] = "damaged_item"
        case["evidence_available"] = False
        case["expected_outcome"] = "request_information"

    elif scenario == "high_value_return":
        case["order_amount"] = round(rng.uniform(15000, 30000), 2)
        case["refund_amount"] = case["order_amount"]
        case["expected_outcome"] = "human_review"

    elif scenario == "contradictory_evidence":
        case["return_reason"] = "item_not_delivered"
        case["risk_label"] = "suspicious"
        case["expected_outcome"] = "human_review"

    return case


def generate_dataset(rows: int, seed: int, output: Path) -> None:
    if rows <= 0:
        raise ValueError("rows must be greater than zero")

    rng = random.Random(seed)
    output.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "case_id",
        "order_id",
        "customer_id",
        "order_amount",
        "refund_amount",
        "days_since_delivery",
        "return_reason",
        "evidence_available",
        "previous_returns_90d",
        "duplicate_request",
        "scenario_type",
        "risk_label",
        "policy_eligible",
        "expected_outcome",
    ]

    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for case_number in range(1, rows + 1):
            writer.writerow(generate_case(case_number, rng))

    print(f"Generated {rows} synthetic return requests.")
    print(f"Random seed: {seed}")
    print(f"Output: {output.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic ReturnGuard test cases."
    )
    parser.add_argument("--rows", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)

    args = parser.parse_args()
    generate_dataset(args.rows, args.seed, args.output)


if __name__ == "__main__":
    main()
