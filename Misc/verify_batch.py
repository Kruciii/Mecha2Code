"""
Validation script for tasks_batch.json
"""
import json
import re

def validate():
    with open("tasks_batch.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "items" in data, "Missing 'items' key"
    assert "dry_run" in data, "Missing 'dry_run' key"
    assert isinstance(data["dry_run"], bool), "'dry_run' must be boolean"
    assert isinstance(data["items"], list), "'items' must be a list"

    print(f"Total items: {len(data['items'])}")

    for idx, item in enumerate(data["items"]):
        assert "module_id" in item, f"Item {idx} missing module_id"
        assert isinstance(item["module_id"], int), f"Item {idx} module_id not int"

        assert "task" in item, f"Item {idx} missing task"
        task = item["task"]
        for field in ["title", "description", "time_limit", "memory_limit"]:
            assert field in task, f"Item {idx} task missing {field}"
            assert task[field] is not None, f"Item {idx} task field {field} is None"

        assert isinstance(task["title"], str) and task["title"].strip()
        assert isinstance(task["description"], str) and task["description"].strip()
        assert isinstance(task["time_limit"], (int, float)) and task["time_limit"] > 0
        assert isinstance(task["memory_limit"], int) and task["memory_limit"] > 0

        assert "test_cases" in item, f"Item {idx} missing test_cases"
        tcs = item["test_cases"]
        assert len(tcs) >= 5, f"Item {idx} has too few test cases: {len(tcs)}"

        has_sample = False
        has_hidden = False

        for tc_idx, tc in enumerate(tcs):
            assert "input_data" in tc, f"Item {idx} tc {tc_idx} missing input_data"
            assert "expected_output" in tc, f"Item {idx} tc {tc_idx} missing expected_output"
            assert "is_hidden" in tc, f"Item {idx} tc {tc_idx} missing is_hidden"

            assert isinstance(tc["input_data"], str)
            assert isinstance(tc["expected_output"], str)
            assert isinstance(tc["is_hidden"], bool)

            if tc["is_hidden"]:
                has_hidden = True
            else:
                has_sample = True

        assert has_sample, f"Item {idx} has no sample test cases"
        assert has_hidden, f"Item {idx} has no hidden test cases"

    print("ALL SCHEMA AND LOGIC VALIDATIONS PASSED PERFECTLY!")

if __name__ == "__main__":
    validate()
