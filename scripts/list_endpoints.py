import sys
sys.path.insert(0, "backend")
from app.main import app

routes = []
for r in app.routes:
    if hasattr(r, "methods") and hasattr(r, "path"):
        methods = ",".join(r.methods)
        routes.append((methods, r.path, r.name))

print(f"Total registered API endpoints: {len(routes)}")
for m, p, n in sorted(routes):
    print(f"  {m:10s} {p:40s} ({n})")

