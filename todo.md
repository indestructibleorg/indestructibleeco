# Step 16 — E2E Tests + CI Enable tests/

## Tasks
- [x] Create tests/e2e/test_service_lifecycle.py (59 tests covering all service layers)
- [x] Add py_compile checks for worker.py, embedding.py, grpc_server.py, health_monitor.py to CI
- [x] Add test_service_lifecycle.py to CI build gate structure check
- [x] Fix sys.path shadowing (use backend.ai.src.* imports instead of sys.path manipulation)
- [x] Verify all 255 tests pass (196 existing + 59 new)
- [x] CI Validator 0 errors, 0 warnings
- [x] Git commit + push
- [ ] CI 5-gate ALL GREEN
