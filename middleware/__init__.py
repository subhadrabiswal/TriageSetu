# Auth is enforced via the get_current_user dependency in
# app/utils/security.py (used with Depends() on each protected
# route) rather than a separate ASGI middleware - this keeps auth
# errors as normal FastAPI HTTPExceptions with clean 401/403 responses.
