"""Final smoke test for MatchIQ backend."""
import sys
sys.path.insert(0, 'backend')

from app.main import app
from app.ml.model_loader import load_model, is_model_loaded, get_model_metadata

loaded = load_model()
print(f"Backend app created: {app.title} v{app.version}")
print(f"Model loaded: {loaded}")

if loaded:
    meta = get_model_metadata()
    print(f"Model: {meta['algorithm']} | acc={meta['accuracy']:.3f} | f1={meta['f1_score']:.3f}")

# Check routes
routes = [r.path for r in app.routes]
required = ['/health', '/teams', '/matches', '/leagues', '/predict']
all_ok = True
for r in required:
    found = any(route.startswith(r) for route in routes)
    status = "OK" if found else "MISSING"
    print(f"  Route {r}: {status}")
    if not found:
        all_ok = False

print()
print("SMOKE TEST RESULT:", "PASS" if all_ok and loaded else "FAIL")
