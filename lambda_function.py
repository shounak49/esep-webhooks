import json, os, base64, urllib.request

def lambda_handler(event, context):
    slack_url = os.environ.get("SLACK_URL", "").strip()
    print("DEBUG start; SLACK_URL set =", bool(slack_url))

    if not slack_url:
        return {"statusCode": 500, "body": "Missing SLACK_URL env var"}

    # Body may be base64 from API Gateway; in console tests it's plain JSON
    body = event.get("body")
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body or b"").decode("utf-8")

    try:
        payload = json.loads(body or "{}")
    except Exception as e:
        print("DEBUG bad JSON in event.body:", repr(e))
        payload = {}

    action = payload.get("action", "opened")
    repo = (payload.get("repository") or {}).get("full_name", "demo/repo")
    issue = payload.get("issue") or {}
    title = issue.get("title", "Hello from Lambda")
    url = issue.get("html_url", "https://example.com/issue/1")
    num = issue.get("number", 1)
    sender = (payload.get("sender") or {}).get("login", "shounak")

    text = f"[{repo}] Issue #{num} {action}: *{title}* by {sender}\n{url}"
    print("DEBUG posting text ->", text)

    data = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(slack_url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.getcode()
            body = (resp.read() or b"").decode("utf-8", "ignore")
            print("DEBUG Slack HTTP =", status, "body =", body)
            # Slack typically returns 200 and "ok"
            ok = (status // 100 == 2)
            return {"statusCode": 200 if ok else 502, "body": f"Slack {status} {body}".strip()}
    except Exception as e:
        print("DEBUG Slack post failed:", repr(e))
        return {"statusCode": 502, "body": f"Slack post failed: {e}"}
