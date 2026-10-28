import json
import os
from dataclasses import dataclass
from urllib import error, request


class Judge0Error(Exception):
    """Raised when Judge0 cannot accept a submission."""


@dataclass(frozen=True)
class Judge0Submission:
    token: str
    status_id: int | None


@dataclass(frozen=True)
class Judge0BatchSubmission:
    token: str
    status_id: int | None


def _request_json(
    *,
    endpoint: str,
    payload: dict | None = None,
    method: str = "POST",
) -> object:
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("JUDGE0_API_KEY")
    if api_key:
        headers["X-Auth-Token"] = api_key

    http_request = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with request.urlopen(http_request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="replace")
        raise Judge0Error(
            f"Judge0 odrzucił zgłoszenie ({exc.code}): {response_body[:500]}"
        ) from exc
    except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise Judge0Error(f"Nie udało się połączyć z Judge0: {exc}") from exc


def get_batch_results(tokens: list[str]) -> list[dict]:
    judge0_url = os.getenv("JUDGE0_URL")
    if not judge0_url:
        raise Judge0Error("Brak zmiennej JUDGE0_URL w pliku .env.")
    if not tokens:
        return []

    endpoint = (
        f"{judge0_url.rstrip('/')}/submissions/batch"
        f"?tokens={','.join(tokens)}"
        "&base64_encoded=false"
    )
    response_data = _request_json(endpoint=endpoint, method="GET")
    if isinstance(response_data, dict):
        response_data = response_data.get("submissions")
    if not isinstance(response_data, list):
        raise Judge0Error("Judge0 zwrócił nieprawidłowe wyniki batcha.")
    return [item for item in response_data if isinstance(item, dict)]


def enqueue_batch(
    *,
    source_code: str,
    language_id: int,
    test_cases: list[dict[str, object]],
) -> list[Judge0BatchSubmission]:
    judge0_url = os.getenv("JUDGE0_URL")
    if not judge0_url:
        raise Judge0Error("Brak zmiennej JUDGE0_URL w pliku .env.")
    if not test_cases:
        raise Judge0Error("Zadanie nie ma przypadków testowych.")

    try:
        batch_size = int(os.getenv("JUDGE0_BATCH_SIZE", "20"))
    except ValueError as exc:
        raise Judge0Error("JUDGE0_BATCH_SIZE musi być liczbą całkowitą.") from exc
    if batch_size < 1:
        raise Judge0Error("JUDGE0_BATCH_SIZE musi być większe od zera.")

    all_submissions: list[Judge0BatchSubmission] = []
    endpoint = (
        f"{judge0_url.rstrip('/')}/submissions/batch"
        "?base64_encoded=false&wait=false"
    )
    for start in range(0, len(test_cases), batch_size):
        batch = test_cases[start : start + batch_size]
        payload = {
            "submissions": [
                {
                    "source_code": source_code,
                    "language_id": language_id,
                    "stdin": test_case["stdin"],
                    "expected_output": test_case["expected_output"],
                    "cpu_time_limit": test_case.get("cpu_time_limit"),
                    "memory_limit": test_case.get("memory_limit"),
                }
                for test_case in batch
            ]
        }
        response_data = _request_json(endpoint=endpoint, payload=payload)
        if not isinstance(response_data, list):
            raise Judge0Error("Judge0 zwrócił nieprawidłową odpowiedź batch.")
        for item in response_data:
            if not isinstance(item, dict) or not item.get("token"):
                raise Judge0Error("Judge0 zwrócił batch bez tokena.")
            status = item.get("status")
            status_id = status.get("id") if isinstance(status, dict) else None
            all_submissions.append(
                Judge0BatchSubmission(
                    token=item["token"],
                    status_id=status_id,
                )
            )

    if len(all_submissions) != len(test_cases):
        raise Judge0Error("Judge0 zwrócił inną liczbę tokenów niż testów.")
    return all_submissions


def enqueue_submission(
    *,
    source_code: str,
    language_id: int,
    stdin: str | None = None,
    expected_output: str | None = None,
) -> Judge0Submission:
    judge0_url = os.getenv("JUDGE0_URL")
    if not judge0_url:
        raise Judge0Error("Brak zmiennej JUDGE0_URL w pliku .env.")

    payload = {
        "source_code": source_code,
        "language_id": language_id,
        "base64_encoded": False,
        "wait": False,
    }
    if stdin is not None:
        payload["stdin"] = stdin
    if expected_output is not None:
        payload["expected_output"] = expected_output

    endpoint = f"{judge0_url.rstrip('/')}/submissions?base64_encoded=false&wait=false"
    response_data = _request_json(endpoint=endpoint, payload=payload)
    if not isinstance(response_data, dict):
        raise Judge0Error("Judge0 zwrócił nieprawidłową odpowiedź.")

    token = response_data.get("token")
    if not token:
        raise Judge0Error("Judge0 zwrócił odpowiedź bez tokena zgłoszenia.")

    return Judge0Submission(
        token=token,
        status_id=response_data.get("status", {}).get("id"),
    )
