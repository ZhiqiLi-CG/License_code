# License-to-Act Commit Protocol

You are operating under a state-changing action license.

Licensed output state:
- Actor role: artifact agent
- Required commit: write `/app/workspace/invoice_summary.xlsx`
- Operation: `WriteOutputWorkbook`
- Required evidence: OCR text from the invoice images and the workbook schema in the task instruction

Protocol:
- First gather enough evidence to determine the required rows.
- Once the output schema is known, stop exploring and commit the workbook.
- Use only non-interactive shell commands. Do not use `nano`, `vim`, `emacs`, or any command that waits for a text editor UI.
- Do not paste raw Python statements directly into the shell. If you need multi-line Python, run it with a quoted here-document, for example `python3 - <<'PY'`.
- After writing the workbook, verify that the file exists, the sheet is named `invoices`, the headers are exactly `filename`, `date`, `total_amount`, and there are 15 data rows.
- Set `task_complete` to true only after that verification.
