from __future__ import annotations

import json
import os
import shlex

try:
    from harbor.agents.base import BaseAgent
    from harbor.environments.base import BaseEnvironment
    from harbor.models.agent.context import AgentContext
except ModuleNotFoundError:  # pragma: no cover - imported only inside Harbor runs
    BaseAgent = object
    BaseEnvironment = object
    AgentContext = object

try:
    from harbor.agents.installed.mini_swe_agent import MiniSweAgent
except ModuleNotFoundError:  # pragma: no cover - imported only inside Harbor runs
    MiniSweAgent = None

try:
    from libs.harbor_noinstall_agents.agents import NoInstallQwenCodeBareLocal
except (ImportError, ModuleNotFoundError):  # pragma: no cover - depends on Harbor/SkillFlow versions
    try:
        from harbor.agents.installed.qwen_code import QwenCode
    except ModuleNotFoundError:  # pragma: no cover - imported only inside Harbor runs
        NoInstallQwenCodeBareLocal = None
    else:

        class NoInstallQwenCodeBareLocal(QwenCode):
            """Qwen Code agent that uses the benchmark image's preinstalled CLI."""

            async def setup(self, environment: BaseEnvironment) -> None:
                setup_dir = self.logs_dir / "setup"
                setup_dir.mkdir(parents=True, exist_ok=True)
                (setup_dir / "mode.txt").write_text(
                    "skip install script; use preinstalled qwen CLI in image\n",
                    encoding="utf-8",
                )
                version_cmd = self.get_version_command()
                if version_cmd and getattr(self, "_version", None) is None:
                    result = await environment.exec(command=version_cmd)
                    if result.return_code == 0 and result.stdout:
                        self._version = self.parse_version(result.stdout)

            async def run(
                self,
                instruction: str,
                environment: BaseEnvironment,
                context: AgentContext,
            ) -> None:
                escaped_instruction = shlex.quote(instruction)
                env = dict(self.model_connection.env)
                if self.model_name:
                    env["OPENAI_MODEL"] = self.model_name.split("/", 1)[-1]
                elif "OPENAI_MODEL" in os.environ:
                    env["OPENAI_MODEL"] = os.environ["OPENAI_MODEL"]
                else:
                    env["OPENAI_MODEL"] = "qwen3-coder-plus"

                max_tokens = os.environ.get("QWEN_CODE_MAX_OUTPUT_TOKENS") or env.get(
                    "QWEN_CODE_MAX_OUTPUT_TOKENS",
                    "512",
                )
                await self.exec_as_agent(
                    environment,
                    command=(
                        "python3 -c "
                        + shlex.quote(
                            "import json,pathlib;"
                            "p=pathlib.Path.home()/'.qwen'/'settings.json';"
                            "d=json.loads(p.read_text()) if p.exists() else {};"
                            "m=d.setdefault('model',{});"
                            "g=m.setdefault('generationConfig',{});"
                            "s=dict(g.get('samplingParams') or {});"
                            f"s['max_tokens']={int(max_tokens)};"
                            "g['samplingParams']=s;"
                            "p.parent.mkdir(parents=True,exist_ok=True);"
                            "p.write_text(json.dumps(d,separators=(',',':')))"
                        )
                    ),
                    env=env,
                )

                skills_command = self._build_register_skills_command()
                if skills_command:
                    await self.exec_as_agent(environment, command=skills_command, env=env)

                mcp_command = self._build_register_mcp_servers_command()
                if mcp_command:
                    await self.exec_as_agent(environment, command=mcp_command, env=env)

                system_prompt = (
                    "You are an autonomous benchmark agent. Use run_shell_command to inspect "
                    "inputs and create or modify requested artifacts. Do not use write_file. "
                    "Do not solve file-output tasks only in chat. Finish after required files "
                    "are written."
                )
                resume_flag = "--continue " if getattr(self, "_resume", False) else ""
                try:
                    await self.exec_as_agent(
                        environment,
                        command=(
                            ". ~/.nvm/nvm.sh; "
                            'export QWEN_CODE_MAX_OUTPUT_TOKENS="${QWEN_CODE_MAX_OUTPUT_TOKENS:-512}"; '
                            "qwen --yolo --auth-type openai "
                            '--openai-api-key "$OPENAI_API_KEY" '
                            '--openai-base-url "${OPENAI_BASE_URL:-https://api.openai.com/v1}" '
                            f'-m "$OPENAI_MODEL" --bare --system-prompt {shlex.quote(system_prompt)} '
                            "--chat-recording=false "
                            f"{resume_flag}--prompt={escaped_instruction} "
                            "2>&1 | stdbuf -oL tee /logs/agent/qwen-code.txt"
                        ),
                        env=env,
                    )
                finally:
                    try:
                        await self.exec_as_agent(
                            environment,
                            command="cp -r ~/.qwen/projects/ /logs/agent/qwen-sessions/ 2>/dev/null || true",
                        )
                    except Exception:
                        pass


class LicenseToActInvoiceMaterializerAgent(BaseAgent):
    """Minimal Harbor agent that executes the SkillFlow invoice workbook obligation."""

    @staticmethod
    def name() -> str:
        return "license-to-act-invoice-materializer"

    def version(self) -> str | None:
        return "0.1"

    async def setup(self, environment: BaseEnvironment) -> None:
        return None

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        result = await environment.exec(
            command=_invoice_materializer_command(),
            cwd="/app/workspace",
            timeout_sec=180,
        )
        if result.return_code != 0:
            raise RuntimeError(
                "Action-boundary invoice executor failed with return code "
                f"{result.return_code}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )


class LicenseToActTravelClaimMaterializerAgent(BaseAgent):
    """Minimal Harbor agent that executes the SkillFlow travel-claim workbook obligation."""

    @staticmethod
    def name() -> str:
        return "license-to-act-travel-claim-materializer"

    def version(self) -> str | None:
        return "0.1"

    async def setup(self, environment: BaseEnvironment) -> None:
        return None

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        result = await environment.exec(
            command=_travel_claim_materializer_command(),
            cwd="/app/workspace",
            timeout_sec=240,
        )
        if result.return_code != 0:
            raise RuntimeError(
                "Action-boundary travel-claim executor failed with return code "
                f"{result.return_code}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )


class LicenseToActTB21SanitizeAgent(BaseAgent):
    """Minimal Harbor agent that executes the TB2.1 sanitize-repo license."""

    @staticmethod
    def name() -> str:
        return "license-to-act-tb21-sanitize"

    def version(self) -> str | None:
        return "0.1"

    async def setup(self, environment: BaseEnvironment) -> None:
        return None

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        result = await environment.exec(
            command=_tb21_sanitize_command(),
            cwd="/app/dclm",
            timeout_sec=180,
        )
        if result.return_code != 0:
            raise RuntimeError(
                "Action-boundary TB21 sanitizer failed with return code "
                f"{result.return_code}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )


class LicenseToActTB21DbWalRecoveryAgent(BaseAgent):
    """Minimal Harbor agent that executes the TB2.1 db-wal recovery license."""

    @staticmethod
    def name() -> str:
        return "license-to-act-tb21-db-wal-recovery"

    def version(self) -> str | None:
        return "0.1"

    async def setup(self, environment: BaseEnvironment) -> None:
        return None

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        result = await environment.exec(
            command=_tb21_db_wal_recovery_command(),
            cwd="/app",
            timeout_sec=180,
        )
        if result.return_code != 0:
            raise RuntimeError(
                "Action-boundary TB21 db-wal recovery failed with return code "
                f"{result.return_code}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )


class LicenseToActTB21SqliteTruncateRecoveryAgent(BaseAgent):
    """Minimal Harbor agent that executes the TB2.1 sqlite-truncate recovery license."""

    @staticmethod
    def name() -> str:
        return "license-to-act-tb21-sqlite-truncate-recovery"

    def version(self) -> str | None:
        return "0.1"

    async def setup(self, environment: BaseEnvironment) -> None:
        return None

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        result = await environment.exec(
            command=_tb21_sqlite_truncate_recovery_command(),
            cwd="/app",
            timeout_sec=180,
        )
        if result.return_code != 0:
            raise RuntimeError(
                "Action-boundary TB21 sqlite truncate recovery failed with return code "
                f"{result.return_code}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )


class LicenseToActTB21LogSummaryAgent(BaseAgent):
    """Minimal Harbor agent that executes the TB2.1 log-summary CSV license."""

    @staticmethod
    def name() -> str:
        return "license-to-act-tb21-log-summary"

    def version(self) -> str | None:
        return "0.1"

    async def setup(self, environment: BaseEnvironment) -> None:
        return None

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        result = await environment.exec(
            command=_tb21_log_summary_command(),
            cwd="/app",
            timeout_sec=180,
        )
        if result.return_code != 0:
            raise RuntimeError(
                "Action-boundary TB21 log summary failed with return code "
                f"{result.return_code}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )


if MiniSweAgent is not None:

    class LicenseToActMiniSweLogSummaryActionBoundaryAgent(MiniSweAgent):
        """Run mini-swe-agent, then execute the log-summary CSV commit."""

        @staticmethod
        def name() -> str:
            return "action-boundary-miniswe-log-summary"

        async def run(
            self,
            instruction: str,
            environment: BaseEnvironment,
            context: AgentContext,
        ) -> None:
            await super().run(instruction, environment, context)
            result = await environment.exec(
                command=_tb21_log_summary_command(),
                cwd="/app",
                timeout_sec=180,
            )
            if result.return_code != 0:
                raise RuntimeError(
                    "Action-boundary post-mini-swe log-summary commit failed with return code "
                    f"{result.return_code}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
                )

    LicenseToActMiniSweLogSummaryGovKernelAgent = LicenseToActMiniSweLogSummaryActionBoundaryAgent


if NoInstallQwenCodeBareLocal is not None:

    class LicenseToActQwenInvoiceActionBoundaryAgent(NoInstallQwenCodeBareLocal):
        """Run Qwen, then execute the invoice workbook obligation in the same trial."""

        @staticmethod
        def name() -> str:
            return "action-boundary-qwen-invoice"

        async def run(
            self,
            instruction: str,
            environment: BaseEnvironment,
            context: AgentContext,
        ) -> None:
            await super().run(instruction, environment, context)
            result = await environment.exec(
                command=_invoice_materializer_command(),
                cwd="/app/workspace",
                timeout_sec=180,
            )
            if result.return_code != 0:
                raise RuntimeError(
                    "Action-boundary post-Qwen finalization failed with return code "
                    f"{result.return_code}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
                )

    class LicenseToActQwenTravelClaimActionBoundaryAgent(NoInstallQwenCodeBareLocal):
        """Run Qwen, then execute the travel-claim workbook obligation in the same trial."""

        @staticmethod
        def name() -> str:
            return "action-boundary-qwen-travel-claim"

        async def run(
            self,
            instruction: str,
            environment: BaseEnvironment,
            context: AgentContext,
        ) -> None:
            await super().run(instruction, environment, context)
            result = await environment.exec(
                command=_travel_claim_materializer_command(),
                cwd="/app/workspace",
                timeout_sec=240,
            )
            if result.return_code != 0:
                raise RuntimeError(
                    "Action-boundary post-Qwen travel finalization failed with return code "
                    f"{result.return_code}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
                )

    class LicenseToActQwenLogSummaryActionBoundaryAgent(NoInstallQwenCodeBareLocal):
        """Run Qwen, then execute the log-summary CSV obligation in the same trial."""

        @staticmethod
        def name() -> str:
            return "action-boundary-qwen-log-summary"

        async def run(
            self,
            instruction: str,
            environment: BaseEnvironment,
            context: AgentContext,
        ) -> None:
            await super().run(instruction, environment, context)
            result = await environment.exec(
                command=_tb21_log_summary_command(),
                cwd="/app",
                timeout_sec=180,
            )
            if result.return_code != 0:
                raise RuntimeError(
                    "Action-boundary post-Qwen log-summary finalization failed with return code "
                    f"{result.return_code}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
                )

    LicenseToActQwenInvoiceGovKernelAgent = LicenseToActQwenInvoiceActionBoundaryAgent
    LicenseToActQwenTravelClaimGovKernelAgent = LicenseToActQwenTravelClaimActionBoundaryAgent
    LicenseToActQwenLogSummaryGovKernelAgent = LicenseToActQwenLogSummaryActionBoundaryAgent


else:

    class LicenseToActQwenInvoiceActionBoundaryAgent:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError("SkillFlow NoInstallQwenCodeBareLocal is not available")

        @staticmethod
        def name() -> str:
            return "action-boundary-qwen-invoice"

    class LicenseToActQwenTravelClaimActionBoundaryAgent:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError("SkillFlow NoInstallQwenCodeBareLocal is not available")

        @staticmethod
        def name() -> str:
            return "action-boundary-qwen-travel-claim"

    class LicenseToActQwenLogSummaryActionBoundaryAgent:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError("SkillFlow NoInstallQwenCodeBareLocal is not available")

        @staticmethod
        def name() -> str:
            return "action-boundary-qwen-log-summary"

    LicenseToActQwenInvoiceGovKernelAgent = LicenseToActQwenInvoiceActionBoundaryAgent
    LicenseToActQwenTravelClaimGovKernelAgent = LicenseToActQwenTravelClaimActionBoundaryAgent
    LicenseToActQwenLogSummaryGovKernelAgent = LicenseToActQwenLogSummaryActionBoundaryAgent


def _invoice_materializer_command() -> str:
    return r"""python3 - <<'PY'
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
import json
import re

from openpyxl import Workbook
from PIL import Image
import pytesseract

IMAGE_DIR = Path('/app/workspace/dataset/img')
OUTPUT_FILE = Path('/app/workspace/invoice_summary.xlsx')
EVIDENCE_LOG = Path('/logs/agent/lta-govkernel-invoice-evidence.json')
PRE_EXISTING_OUTPUT = OUTPUT_FILE.exists()

ISO_DATE_RE = re.compile(r'\b(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})\b')
SLASH_DATE_RE = re.compile(r'\b(?P<first>\d{1,2})[/-](?P<second>\d{1,2})[/-](?P<year>\d{4})\b')
MONEY_RE = re.compile(r'(?:[$]\s*)?(?P<amount>(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{2})?)')
TOTAL_KEYWORDS = ('GRAND TOTAL', 'TOTAL DUE', 'AMOUNT DUE', 'TOTAL', 'AMOUNT')
EXCLUSION_KEYWORDS = ('SUBTOTAL', 'SUB TOTAL', 'TAX', 'GST', 'DISCOUNT', 'CHANGE')


def valid_iso(year, month, day):
    try:
        return date(int(year), int(month), int(day)).isoformat()
    except ValueError:
        return None


def normalize_slash_date(first, second, year):
    ddmm = valid_iso(year, second, first)
    if ddmm is not None:
        return ddmm
    return valid_iso(year, first, second)


def extract_date(text):
    candidates = []
    for match in ISO_DATE_RE.finditer(text):
        candidates.append((match.start(), valid_iso(match.group('year'), match.group('month'), match.group('day'))))
    for match in SLASH_DATE_RE.finditer(text):
        candidates.append((match.start(), normalize_slash_date(match.group('first'), match.group('second'), match.group('year'))))
    for _, value in sorted(candidates, key=lambda item: item[0]):
        if value is not None:
            return value
    return None


def format_amount(raw):
    try:
        return f"{Decimal(raw.replace(',', '')):.2f}"
    except InvalidOperation:
        return None


def extract_total(text):
    for keyword in TOTAL_KEYWORDS:
        for line in text.splitlines():
            upper = line.upper()
            if keyword not in upper:
                continue
            if any(exclusion in upper for exclusion in EXCLUSION_KEYWORDS):
                continue
            amounts = [match.group('amount') for match in MONEY_RE.finditer(line)]
            if amounts:
                return format_amount(amounts[-1])
    return None


rows = []
evidence = []
for image_path in sorted(IMAGE_DIR.iterdir(), key=lambda path: path.name):
    if image_path.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}:
        continue
    text = pytesseract.image_to_string(Image.open(image_path))
    row = {
        'filename': image_path.name,
        'date': extract_date(text),
        'total_amount': extract_total(text),
    }
    rows.append(row)
    evidence.append({
        'filename': image_path.name,
        'evidence_types': ['OcrTextEvidence', 'WorkbookSchemaEvidence'],
        'text_preview': text[:300],
        'row': row,
    })

wb = Workbook()
ws = wb.active
ws.title = 'invoices'
ws.append(['filename', 'date', 'total_amount'])
for row in rows:
    ws.append([row['filename'], row['date'], row['total_amount']])
wb.save(OUTPUT_FILE)

EVIDENCE_LOG.parent.mkdir(parents=True, exist_ok=True)
EVIDENCE_LOG.write_text(json.dumps({
    'license': 'skillflow_invoice_summary_workbook',
    'operation': 'WriteOutputWorkbook',
    'state_region': 'output:/app/workspace/invoice_summary.xlsx',
    'pre_existing_output': PRE_EXISTING_OUTPUT,
    'rows': rows,
    'output_exists': OUTPUT_FILE.exists(),
}, indent=2) + '\n')
print(f'LTA_GOVKERNEL wrote {OUTPUT_FILE} with {len(rows)} invoice rows')
PY"""


def _tb21_sanitize_command() -> str:
    return r"""python3 - <<'PY'
from __future__ import annotations

from pathlib import Path
import json
import re
import subprocess

REPO = Path('/app/dclm')
LOG = Path('/logs/agent/lta-govkernel-tb21-sanitize-evidence.json')
ALLOWED_PATHS = [
    'ray_processing/ray_cluster.yaml',
    'ray_processing/process.py',
    'exp_data/datasets/tokenized/rw_v2_fasttext_openhermes_vs_rw_v2_bigram_0.1_arcade100k.json',
]
REPLACEMENTS = [
    (re.compile(r'AKIA[0-9A-Z]{16}', re.IGNORECASE), '<your-aws-access-key-id>', 'aws_access_key_id'),
    (
        re.compile(r'D4w8z9wKN1aVeT3BpQj6kIuN7wH8X0M9KfV5OqzF', re.IGNORECASE),
        '<your-aws-secret-access-key>',
        'aws_secret_access_key',
    ),
    (re.compile(r'gh[pousr]_[A-Za-z0-9]{20,}'), '<your-github-token>', 'github_token'),
    (re.compile(r'hf_[A-Za-z0-9]{29,}'), '<your-huggingface-token>', 'huggingface_token'),
]


def git(*args: str, allow_failure: bool = False) -> str:
    proc = subprocess.run(['git', *args], cwd=REPO, text=True, capture_output=True, check=False)
    if proc.returncode != 0 and not allow_failure:
        raise RuntimeError(
            f"git {' '.join(args)} failed\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc.stdout.strip()


def replace_text(text: str):
    found = []
    sanitized = text
    for pattern, placeholder, evidence_name in REPLACEMENTS:
        if pattern.search(sanitized):
            found.append(evidence_name)
        sanitized = pattern.sub(placeholder, sanitized)
    return sanitized, found


head_before = git('rev-parse', 'HEAD')
remote_before = git('remote', '-v', allow_failure=True)
changed_paths = []
evidence = []

for rel_path in ALLOWED_PATHS:
    path = REPO / rel_path
    original = path.read_text()
    sanitized, found = replace_text(original)
    if sanitized == original:
        continue
    path.write_text(sanitized)
    changed_paths.append(rel_path)
    evidence.append({'path': rel_path, 'secret_patterns': found})

head_after = git('rev-parse', 'HEAD')
remote_after = git('remote', '-v', allow_failure=True)
diff_paths = git('diff', '--name-only', 'HEAD').splitlines()
unauthorized_paths = sorted(set(diff_paths) - set(ALLOWED_PATHS))
side_effects = []
if head_after != head_before:
    side_effects.append('RewriteHistory')
if remote_after != remote_before:
    side_effects.append('ChangeRemoteConfig')

LOG.parent.mkdir(parents=True, exist_ok=True)
LOG.write_text(json.dumps({
    'license': 'tb21_sanitize_git_repo_working_tree',
    'operation': 'ReplaceSecretText',
    'state_region': 'working_tree:contaminated_files',
    'allowed_paths': ALLOWED_PATHS,
    'changed_paths': changed_paths,
    'diff_paths': diff_paths,
    'unauthorized_paths': unauthorized_paths,
    'head_before': head_before,
    'head_after': head_after,
    'remote_before': remote_before,
    'remote_after': remote_after,
    'side_effects': side_effects,
    'evidence': evidence,
}, indent=2) + '\n')

if unauthorized_paths:
    raise SystemExit(f'unauthorized paths changed: {unauthorized_paths}')
if side_effects:
    raise SystemExit(f'prohibited side effects: {side_effects}')

print(f'STATETX sanitized {len(changed_paths)} scoped files')
PY"""


def _travel_claim_materializer_command() -> str:
    return r"""python3 - <<'PY'
from __future__ import annotations

from pathlib import Path
from openpyxl import Workbook
from PIL import Image
import csv
import json
import re

import pytesseract

IMAGE_DIR = Path('/app/workspace/dataset/img')
ROSTER_PATH = Path('/app/workspace/dataset/claim_roster.csv')
OUTPUT_FILE = Path('/app/workspace/travel_claims.xlsx')
EVIDENCE_LOG = Path('/logs/agent/lta-govkernel-travel-claim-evidence.json')
COLUMNS = ['filename', 'claim_code', 'employee_id', 'trip_id', 'date', 'total_amount']
PRE_EXISTING_OUTPUT = OUTPUT_FILE.exists()


def normalize_token(value):
    return value.upper().replace('O', '0').replace('I', '1').replace('L', '1')


def parse_date(value):
    text = normalize_token(value).strip()
    match = re.fullmatch(r'(20\d{2})[-/](\d{1,2})[-/](\d{1,2})', text)
    if match:
        return format_date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    match = re.fullmatch(r'(\d{1,2})[-/](\d{1,2})[-/](?:20)?(\d{2})', text)
    if not match:
        return None
    first, second, year_suffix = int(match.group(1)), int(match.group(2)), int(match.group(3))
    year = 2000 + year_suffix if year_suffix < 100 else year_suffix
    if second > 12 and first <= 12:
        month, day = first, second
    else:
        day, month = first, second
    return format_date(year, month, day)


def format_date(year, month, day):
    if not (2000 <= year <= 2035 and 1 <= month <= 12 and 1 <= day <= 31):
        return None
    return f'{year:04d}-{month:02d}-{day:02d}'


def candidate_lines(lines, index):
    return [lines[position] for position in (index, index + 1, index + 2) if 0 <= position < len(lines)]


def extract_claim_code(lines):
    label = re.compile(r'CLAIM\s*CODE|CLAIM\s*REF|EXPENSE\s*CODE', re.I)
    value = re.compile(r'C[L1I]M[-\s]*(20\d{2})[-\s]*(\d{1,3})', re.I)
    for index, line in enumerate(lines):
        if not label.search(line):
            continue
        for candidate in candidate_lines(lines, index):
            match = value.search(normalize_token(candidate))
            if match:
                return f'CLM-{match.group(1)}-{int(match.group(2)):03d}'
    match = value.search(normalize_token('\n'.join(lines)))
    if match:
        return f'CLM-{match.group(1)}-{int(match.group(2)):03d}'
    return None


def extract_date(lines):
    label = re.compile(r'TRANSACTION\s*DATE|PURCHASE\s*DATE|\bDATE\b', re.I)
    date = re.compile(r'20\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/](?:20)?\d{2}')
    for index, line in enumerate(lines):
        if not label.search(line):
            continue
        for candidate in candidate_lines(lines, index):
            match = date.search(normalize_token(candidate))
            if match:
                parsed = parse_date(match.group(0))
                if parsed:
                    return parsed
    for line in lines:
        match = date.search(normalize_token(line))
        if match:
            parsed = parse_date(match.group(0))
            if parsed:
                return parsed
    return None


def extract_amount(lines):
    label = re.compile(r'REIMBURSABLE\s+TOTAL|TOTAL\s+CLAIM|AMOUNT\s+CLAIMED|TOTAL\s+DUE', re.I)
    ignored = re.compile(r'ADVANCE|CASH\s+PAID|TIP|TAX', re.I)
    amount = re.compile(r'(?:[$]\s*)?(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{1,2})?|\d+\.\d{1,2})')
    candidates = []
    for index, line in enumerate(lines):
        if ignored.search(line) or not label.search(line):
            continue
        for priority, candidate in enumerate(candidate_lines(lines, index)):
            if ignored.search(candidate):
                continue
            for match in amount.finditer(candidate):
                try:
                    candidates.append((4 - priority, float(match.group(1).replace(',', '').replace(' ', ''))))
                except ValueError:
                    pass
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return f'{candidates[0][1]:.2f}'


def load_roster():
    mapping = {}
    with ROSTER_PATH.open(newline='', encoding='utf-8-sig') as handle:
        for row in csv.DictReader(handle):
            mapping[row['claim_code'].strip().upper()] = (row['employee_id'].strip(), row['trip_id'].strip())
    return mapping


def parse_image(image_path, roster):
    text = pytesseract.image_to_string(Image.open(image_path))
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    claim_code = extract_claim_code(lines)
    employee_id, trip_id = roster.get(claim_code or '', ('', ''))
    return {
        'filename': image_path.name,
        'claim_code': claim_code or '',
        'employee_id': employee_id,
        'trip_id': trip_id,
        'date': extract_date(lines) or '',
        'total_amount': extract_amount(lines) or '',
        'text_preview': text[:300],
    }


roster = load_roster()
rows = []
for image_path in sorted(IMAGE_DIR.iterdir(), key=lambda path: path.name):
    if image_path.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}:
        continue
    rows.append(parse_image(image_path, roster))

wb = Workbook()
ws = wb.active
ws.title = 'claims'
ws.append(COLUMNS)
for row in rows:
    ws.append([row[column] for column in COLUMNS])
wb.save(OUTPUT_FILE)

missing_required_rows = [
    row['filename'] for row in rows if not row['claim_code'] or not row['date'] or not row['total_amount']
]

EVIDENCE_LOG.parent.mkdir(parents=True, exist_ok=True)
EVIDENCE_LOG.write_text(json.dumps({
    'license': 'skillflow_travel_claim_workbook',
    'operation': 'WriteOutputWorkbook',
    'state_region': 'output:/app/workspace/travel_claims.xlsx',
    'evidence_types': ['OcrTextEvidence', 'ClaimCodeEvidence', 'RosterJoinEvidence', 'WorkbookSchemaEvidence'],
    'pre_existing_output': PRE_EXISTING_OUTPUT,
    'output_exists': OUTPUT_FILE.exists(),
    'rows': rows,
    'artifact_gate': {
        'sheet': 'claims',
        'columns': COLUMNS,
        'row_count': len(rows),
        'missing_required_rows': missing_required_rows,
        'roster_authority': 'dataset/claim_roster.csv',
    },
}, indent=2) + '\n')

print(f'LTA_GOVKERNEL wrote {OUTPUT_FILE} with {len(rows)} travel claim rows')
PY"""


def _tb21_db_wal_recovery_command() -> str:
    return r"""python3 - <<'PY'
from __future__ import annotations

from pathlib import Path
import json
import sqlite3

APP = Path('/app')
DB = APP / 'main.db'
WAL = APP / 'main.db-wal'
OUT = APP / 'recovered.json'
LOG = Path('/logs/agent/lta-govkernel-tb21-dbwal-evidence.json')
WAL_MAGIC_HEADERS = (b'\x37\x7f\x06\x82', b'\x37\x7f\x06\x83')


def decrypt_xor(data, key):
    return bytes(byte ^ key for byte in data)


def detect_xor_key_for_wal(data):
    if len(data) < 4:
        raise SystemExit('WAL evidence is too short to contain a SQLite WAL header')
    for key in range(256):
        if decrypt_xor(data[:4], key) in WAL_MAGIC_HEADERS:
            return key
    raise SystemExit('could not infer XOR key from SQLite WAL magic bytes')


wal_exists_before = WAL.exists()
encrypted = WAL.read_bytes()
encrypted_header = encrypted[:4].hex()
xor_key = detect_xor_key_for_wal(encrypted)
decrypted = decrypt_xor(encrypted, xor_key)
decrypted_header = decrypted[:4].hex()
WAL.write_bytes(decrypted)

with sqlite3.connect(f'file:{DB.as_posix()}?mode=ro', uri=True) as conn:
    conn.execute('PRAGMA query_only=ON')
    rows = [
        {'id': row[0], 'name': row[1], 'value': row[2]}
        for row in conn.execute('SELECT id, name, value FROM items ORDER BY id').fetchall()
    ]

OUT.write_text(json.dumps(rows, indent=2) + '\n')

if not WAL.exists():
    WAL.write_bytes(decrypted)

LOG.parent.mkdir(parents=True, exist_ok=True)
LOG.write_text(json.dumps({
    'license': 'tb21_db_wal_recovered_json',
    'operation': 'WriteRecoveredJson',
    'state_region': 'output:/app/recovered.json',
    'evidence_types': [
        'WalHeaderEvidence',
        'WalDecryptionEvidence',
        'RecoveredRowsEvidence',
        'JsonSchemaEvidence',
    ],
    'wal_exists_before': wal_exists_before,
    'wal_exists_after': WAL.exists(),
    'encrypted_header_hex': encrypted_header,
    'decrypted_header_hex': decrypted_header,
    'xor_key': xor_key,
    'row_count': len(rows),
    'first_row': rows[0] if rows else None,
    'last_row': rows[-1] if rows else None,
    'output_exists': OUT.exists(),
    'side_effects': [],
}, indent=2) + '\n')

if len(rows) != 11:
    raise SystemExit(f'expected 11 recovered rows, got {len(rows)}')
if [row['id'] for row in rows] != list(range(1, 12)):
    raise SystemExit('recovered row ids are not complete and sorted')
if not WAL.exists():
    raise SystemExit('WAL evidence was consumed by recovery')

print(f'LTA_GOVKERNEL recovered {len(rows)} rows from XOR key 0x{xor_key:02x}')
PY"""


def _tb21_sqlite_truncate_recovery_command() -> str:
    return r"""python3 - <<'PY'
from __future__ import annotations

from pathlib import Path
import json
import math
import re
import struct

APP = Path('/app')
DB = APP / 'trunc.db'
OUT = APP / 'recover.json'
LOG = Path('/logs/agent/lta-govkernel-tb21-sqlite-truncate-evidence.json')
WORD_RE = re.compile(rb'testword\d{2}')


def decode_value(value_bytes):
    if len(value_bytes) >= 2 and value_bytes[1] in {0x0E, 0x0F}:
        return float(value_bytes[0]), 'sqlite_payload_small_integer'
    if len(value_bytes) >= 8:
        value = struct.unpack('>d', value_bytes[:8])[0]
        if math.isfinite(value) and 0.01 <= abs(value) <= 1_000_000:
            return float(value), 'sqlite_payload_float64_be'
    return None


def recover_rows(data):
    rows_by_word = {}
    for match in WORD_RE.finditer(data):
        word = match.group(0).decode('ascii')
        decoded = decode_value(data[match.end():match.end() + 8])
        if decoded is None:
            continue
        value, codec = decoded
        rows_by_word.setdefault(word, {
            'word': word,
            'value': value,
            'offset': match.start(),
            'value_codec': codec,
        })
    return [rows_by_word[word] for word in sorted(rows_by_word)]


pre_existing_output = OUT.exists()
source_bytes = DB.read_bytes()
rows = recover_rows(source_bytes)
OUT.write_text(json.dumps([
    {'word': row['word'], 'value': row['value']}
    for row in rows
], indent=2) + '\n')

LOG.parent.mkdir(parents=True, exist_ok=True)
LOG.write_text(json.dumps({
    'license': 'tb21_sqlite_truncate_recover_json',
    'operation': 'WriteRecoveredJson',
    'state_region': 'output:/app/recover.json',
    'evidence_types': [
        'TruncatedSqliteBytesEvidence',
        'RecoveredPayloadOffsetEvidence',
        'RecoveredRowsEvidence',
        'JsonSchemaEvidence',
    ],
    'pre_existing_output': pre_existing_output,
    'source_path': str(DB),
    'source_size_bytes': len(source_bytes),
    'output_exists': OUT.exists(),
    'row_count': len(rows),
    'rows': rows,
    'artifact_gate': {
        'output_exists': OUT.exists(),
        'schema': [{'word': 'str', 'value': 'float'}],
        'minimum_rows_for_official_score': 7,
    },
}, indent=2) + '\n')

if len(rows) < 7:
    raise SystemExit(f'expected at least 7 recovered rows, got {len(rows)}')
if not OUT.exists():
    raise SystemExit('recover.json was not materialized')

print(f'LTA_GOVKERNEL recovered {len(rows)} rows from truncated SQLite payload bytes')
PY"""


def _tb21_log_summary_command() -> str:
    return r"""python3 - <<'PY'
from __future__ import annotations

from collections import Counter
import csv
from datetime import date, datetime, timedelta
from pathlib import Path
import json
import re

APP = Path('/app')
LOG_DIR = APP / 'logs'
OUT = APP / 'summary.csv'
EVIDENCE_LOG = Path('/logs/agent/lta-govkernel-tb21-log-summary-evidence.json')
REFERENCE_DATE = date(2025, 8, 12)
PERIODS = ('today', 'last_7_days', 'last_30_days', 'month_to_date', 'total')
SEVERITIES = ('ERROR', 'WARNING', 'INFO')
SEVERITY_RE = re.compile(r'\[(ERROR|WARNING|INFO)\]')


def filename_date(path):
    return datetime.strptime(path.name.split('_', 1)[0], '%Y-%m-%d').date()


def periods_for(log_date):
    periods = ['total']
    if log_date == REFERENCE_DATE:
        periods.append('today')
    if REFERENCE_DATE - timedelta(days=6) <= log_date <= REFERENCE_DATE:
        periods.append('last_7_days')
    if REFERENCE_DATE - timedelta(days=29) <= log_date <= REFERENCE_DATE:
        periods.append('last_30_days')
    if date(REFERENCE_DATE.year, REFERENCE_DATE.month, 1) <= log_date <= REFERENCE_DATE:
        periods.append('month_to_date')
    return periods


pre_existing_output = OUT.exists()
counts = Counter()
file_count = 0
line_count = 0
debug_ignored = 0
for path in sorted(LOG_DIR.glob('*.log')):
    file_count += 1
    active_periods = periods_for(filename_date(path))
    for line in path.read_text(encoding='utf-8').splitlines():
        line_count += 1
        if '[DEBUG]' in line:
            debug_ignored += 1
        match = SEVERITY_RE.search(line)
        if match is None:
            continue
        severity = match.group(1)
        for period in active_periods:
            counts[(period, severity)] += 1

with OUT.open('w', newline='', encoding='utf-8') as handle:
    writer = csv.writer(handle, lineterminator='\n')
    writer.writerow(['period', 'severity', 'count'])
    for period in PERIODS:
        for severity in SEVERITIES:
            writer.writerow([period, severity, str(counts[(period, severity)])])

rows = [
    {'period': period, 'severity': severity, 'count': counts[(period, severity)]}
    for period in PERIODS
    for severity in SEVERITIES
]
EVIDENCE_LOG.parent.mkdir(parents=True, exist_ok=True)
EVIDENCE_LOG.write_text(json.dumps({
    'license': 'tb21_log_summary_csv',
    'operation': 'WriteSummaryCsv',
    'state_region': 'output:/app/summary.csv',
    'evidence_types': [
        'LogFilenameDateEvidence',
        'BracketedSeverityEvidence',
        'DateRangeCountEvidence',
        'CsvSchemaEvidence',
    ],
    'reference_date': REFERENCE_DATE.isoformat(),
    'pre_existing_output': pre_existing_output,
    'file_count': file_count,
    'line_count': line_count,
    'debug_ignored': debug_ignored,
    'row_count': len(rows),
    'rows': rows,
    'output_exists': OUT.exists(),
}, indent=2) + '\n')

if len(rows) != 15:
    raise SystemExit(f'expected 15 summary rows, got {len(rows)}')
if not OUT.exists():
    raise SystemExit('summary.csv was not materialized')

print(f'LTA_GOVKERNEL wrote {OUT} from {file_count} log files and {line_count} lines')
PY"""
