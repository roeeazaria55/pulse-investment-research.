"""One fixed GET for model metadata; no generation, retries, files or raw output.

API reference: https://developers.openai.com/api/reference/resources/models/methods/retrieve
Success proves metadata access, NOT billing credit or Responses permission.
Use only after the protected workflow's current-run approval gate.
"""
import json
import os
import urllib.error
import urllib.request

MODEL = "gpt-6.1-sol"
URL = "https://api.openai.com/v1/models/" + MODEL


class CheckError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CheckError("redirect-refused")


def check_connection():
    if os.getenv("PAID_AI_ENABLED") != "NO":
        raise CheckError("paid-switch-must-be-NO")
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        raise CheckError("secret-missing")
    if key != key.strip() or any(ord(c) < 33 or ord(c) > 126 for c in key):
        raise CheckError("secret-format-invalid")
    request = urllib.request.Request(URL, method="GET", headers={
        "Authorization": "Bearer " + key,
        "Accept": "application/json",
        "User-Agent": "PULSE-connection-check",
    })
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=20) as response:
            if response.status != 200:
                raise CheckError("unexpected-http-status")
            raw = response.read(65537)
            if len(raw) > 65536:
                raise CheckError("response-too-large")
            payload = json.loads(raw)
    except urllib.error.HTTPError as error:
        # Do not read or log the body: providers may echo credentials in errors.
        code = {401: "authentication-rejected", 403: "permission-denied",
                404: "model-unavailable-or-not-permitted", 429: "rate-or-quota-limited"}.get(
                    error.code, "provider-http-error")
        raise CheckError(code) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise CheckError("network-or-tls-failure") from None
    except (ValueError, UnicodeError):
        raise CheckError("invalid-response") from None
    if not isinstance(payload, dict) or payload.get("object") != "model" or payload.get("id") != MODEL:
        raise CheckError("unexpected-model-response")
    return {"status": "authenticated-model-metadata-readable", "model": MODEL,
            "generationExecuted": False, "billingVerified": False,
            "responsesPermissionVerified": False, "publicationExecuted": False}


def main():
    try:
        result = check_connection()
    except CheckError as error:
        print(json.dumps({"status": "blocked", "reason": str(error), "generationExecuted": False}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
