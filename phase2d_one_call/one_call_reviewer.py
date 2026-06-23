import os
import sys
import json

REQUIRED = ("message_id", "verdict", "safety_class_confirmed", "notes", "next_action")
ALLOWED_VERDICTS = ("continue", "hold", "needs_owner", "blocked_red")
ALLOWED_CLASSES = ("GREEN", "YELLOW", "RED")

def preflight():
    if not os.environ.get("OPENAI_API_KEY"):
        return "blocked_no_key"
    if os.environ.get("RELAY_CONFIRM_API") != "1":
        return "blocked_no_confirm"
    if os.environ.get("RELAY_ENV") != "phase2_test":
        return "blocked_wrong_env"
    return "ok"

def main():
    status = preflight()
    if status != "ok":
        print(f"PREFLIGHT {status}: refusing to call. No request made.")
        sys.exit(2)

    from openai import OpenAI

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    test_message = {
        "id": "phase2d-smoke-1",
        "safety_class": "GREEN",
        "body": "Non-sensitive connectivity smoke test for the relay reviewer."
    }

    system_prompt = (
        "You are the relay handoff reviewer. "
        "Respond with STRICT JSON only, no prose. "
        "Use exactly these keys: message_id, verdict, safety_class_confirmed, notes, next_action. "
        "verdict must be one of: continue, hold, needs_owner, blocked_red. "
        "safety_class_confirmed must be one of: GREEN, YELLOW, RED."
    )

    client = OpenAI(timeout=30)

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(test_message)}
        ],
        response_format={"type": "json_object"},
        temperature=0
    )

    content = resp.choices[0].message.content

    try:
        obj = json.loads(content)
    except Exception:
        print("INVALID: response was not valid JSON.")
        print(content)
        sys.exit(1)

    valid = (
        isinstance(obj, dict)
        and all(k in obj for k in REQUIRED)
        and obj.get("verdict") in ALLOWED_VERDICTS
        and obj.get("safety_class_confirmed") in ALLOWED_CLASSES
    )

    print("ONE_CALL_RESULT:")
    print(json.dumps(obj, ensure_ascii=False, indent=2))
    print("VALID_STRUCTURE:", valid)
    print("No DB touched. No key/env/headers printed. Exactly one request made.")

    sys.exit(0 if valid else 1)

if __name__ == "__main__":
    main()
