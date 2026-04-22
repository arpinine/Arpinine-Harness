---
rule-id: arch-001
category: architecture
triggers:
  - HTTP request/response objects (Request, Response, HttpServletRequest) imported in non-handler files
  - framework-specific types appear in files outside the designated handler/controller layer
prevents: business logic coupled to HTTP transport layer, blocking testability and future framework changes
source-adr: ~
evidence-project: example
severity: HIGH
active: true
---

## Rule

Business logic modules must not import or reference HTTP transport types. If a file in `src/domain/`, `src/services/`, or `src/use-cases/` imports an HTTP type, it violates the module boundary defined in `plan.md`.

## Detection Pattern

Files in non-handler paths (not `src/api/`, `src/handlers/`, `src/routes/`, `src/controllers/`) that contain:
- Import of `Request`, `Response`, `HttpServletRequest`, `flask.request`, `fastapi.Request`
- Direct use of `req.body`, `res.json()`, `ctx.params` outside handler layer

## Correct Pattern

Handler layer extracts data from the request and passes plain values to the business logic:

```python
# handlers/login_handler.py  ← HTTP layer
def handle_login(req: Request) -> Response:
    credentials = LoginCredentials(email=req.json["email"], password=req.json["password"])
    result = login_use_case.execute(credentials)  # ← plain value, no HTTP object
    return jsonify(result.to_dict()), 200
```
