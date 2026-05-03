from starlette.responses import Response

def parse_csv_setting(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]

def add_security_headers(response: Response) -> Response:
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")

    # Keep CSP conservative but API-friendly. Frontend CSP should be handled
    # separately by Next.js or the edge/proxy if needed.
    response.headers.setdefault("Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'")

    return response
