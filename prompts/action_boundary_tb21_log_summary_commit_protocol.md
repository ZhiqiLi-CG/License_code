# Action Boundary Log Summary Commit Protocol

Required output:
- Write `/app/summary.csv`.
- The CSV must have rows for `today`, `last_7_days`, `last_30_days`, `month_to_date`, and `total`.
- The columns must be `range`, `ERROR`, `WARNING`, and `INFO`.

Execution rule:
- Inspect the task files and logs.
- Compute counts from the log files, excluding DEBUG entries.
- After the output file is ready, verify the file exists and has the exact header and five rows.
- Mark the task complete only after the CSV has been written.

Use only non-interactive shell commands. Do not use a terminal editor.
