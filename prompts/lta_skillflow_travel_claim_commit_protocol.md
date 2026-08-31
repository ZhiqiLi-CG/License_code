# StateTx Travel-Claim Commit Protocol

You are operating under a state-changing transaction contract.

Licensed output state:
- Actor role: artifact agent
- Required commit: write `/app/workspace/travel_claims.xlsx`
- Operation: `WriteOutputWorkbook`
- Required evidence: OCR text from the travel claim images, `dataset/claim_roster.csv`, and the workbook schema in the task instruction

Protocol:
- First gather enough evidence to identify the required rows.
- Treat the roster as the authoritative source for `employee_id` and `trip_id`.
- Once the output schema is known, stop exploring and commit the workbook.
- Use only non-interactive shell commands. Do not use `nano`, `vim`, `emacs`, or any command that waits for a text editor UI.
- Do not paste raw Python statements directly into the shell. If you need multi-line Python, run it with a quoted here-document, for example `python3 - <<'PY'`.
- After writing the workbook, verify that the file exists, the sheet is named `claims`, the headers are exactly `filename`, `claim_code`, `employee_id`, `trip_id`, `date`, `total_amount`, and there are 16 data rows.
- Set `task_complete` to true only after that verification.
