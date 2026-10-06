# Execution (Layer 3: Deterministic Tools)

Deterministic Python scripts live here.

## Principles
1. **Deterministic & Testable**: Scripts should handle APIs, data parsing, database or file actions predictably.
2. **Environment Variables**: Load secrets and configurations from `.env` using `python-dotenv`.
3. **Intermediates vs Deliverables**:
   - Write intermediate files to `.tmp/`.
   - Deliverables should be uploaded/synced to cloud services (Google Sheets, Slides, cloud DBs, etc.).
4. **Self-Annealing**: If a script errors out, diagnose the stack trace, update the script, verify the fix, and update the associated directive in `directives/`.
