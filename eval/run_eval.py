import os
from helpdesk.agent import HelpdeskAgent

EVAL_DATASET = [
    {
        "id": 1,
        "question": "What time do you open on Saturday in June?",
        "expected_facts": ["08:00"],
        "should_refuse": False
    },
    {
        "id": 2,
        "question": "How much does an e-bike cost per day?",
        "expected_facts": ["40"],
        "should_refuse": False
    },
    {
        "id": 3,
        "question": "I want to cancel booking CW-1001. How much will I get back?",
        "expected_facts": ["90"],
        "should_refuse": False
    },
    {
        "id": 4,
        "question": "What is the refund for booking CW-1002 if I cancel now?",
        "expected_facts": ["340"],
        "should_refuse": False
    },
    {
        "id": 5,
        "question": "Can I cancel booking CW-1003 and how much refund do I get?",
        "expected_facts": ["50"],
        "should_refuse": False
    },
    {
        "id": 6,
        "question": "What is the status and refund amount for booking CW-1008?",
        "expected_facts": ["in_progress", "0"],
        "should_refuse": False
    },
    {
        "id": 7,
        "question": "What is the deposit amount for renting a city bike?",
        "expected_facts": ["50"],
        "should_refuse": False
    },
    {
        "id": 8,
        "question": "Can a 10-year-old rent an e-bike alone?",
        "expected_facts": ["16"],
        "should_refuse": False
    },
    {
        "id": 9,
        "question": "What is the capital of Australia?",
        "expected_facts": ["help@citywheels.example"],
        "should_refuse": True
    },
    {
        "id": 10,
        "question": "What will the weather be like tomorrow in Warsaw?",
        "expected_facts": ["contact", "staff"],
        "should_refuse": True
    }
]


def run_evaluation():
    agent = HelpdeskAgent()
    passed = 0
    results = []

    print("Running evaluation suite...\n")

    for case in EVAL_DATASET:
        response = agent.run(case["question"])

        # Verify facts presence
        facts_passed = all(fact.lower() in response.lower() for fact in case["expected_facts"])

        status = "PASS" if facts_passed else "FAIL"
        if facts_passed:
            passed += 1

        results.append({
            "id": case["id"],
            "question": case["question"],
            "response": response,
            "status": status
        })

        print(f"[{status}] Q{case['id']}: {case['question']}")

    summary = f"\nEvaluation Completed: {passed}/{len(EVAL_DATASET)} passed."
    print(summary)

    # Save output report to eval/results.md
    os.makedirs("eval", exist_ok=True)
    with open("eval/results.md", "w", encoding="utf-8") as f:
        f.write(f"# Evaluation Results\n\n**Score:** {passed}/{len(EVAL_DATASET)} passed\n\n")
        f.write("| ID | Question | Status | Answer Snippet |\n")
        f.write("|---|---|---|---|\n")
        for r in results:
            clean_resp = r["response"].replace("\n", " ")[:80] + "..."
            f.write(f"| {r['id']} | {r['question']} | {r['status']} | {clean_resp} |\n")


if __name__ == "__main__":
    run_evaluation()