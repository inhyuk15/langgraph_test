# fs_llm_tools.py
from __future__ import annotations

import difflib
import hashlib
import os
from pathlib import Path
from typing import Literal, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field, model_validator

# ===== 설정 =====
ROOT_DIR = Path(os.getenv("WORKSPACE", ".")).resolve()

# ===== BaseModel =====
class ToolMeta(BaseModel):
    function_name: str = Field(..., description="name of the tool used")
    parameters: dict = Field(..., description="parameters passed to the tool")

class ReadFileResult(BaseModel):
    """read_file 결과"""
    status: Literal["ok", "error"]
    message: str
    path: Optional[str] = None
    total_lines: Optional[int] = None
    sha256: Optional[str] = None
    content: Optional[str] = None
    meta: Optional[ToolMeta] = None  # 모든 분기에서 채워 반환

class EditSummary(BaseModel):
    description: str
    affected_lines: list[int]

class WriteFileResult(BaseModel):
    """write_file 결과"""
    status: Literal["ok", "conflict", "noop", "error"]
    message: str
    path: Optional[str] = None
    new_sha256: Optional[str] = None
    diff_unified: Optional[str] = None
    summaries: list[EditSummary] = Field(default_factory=list)
    meta: Optional[ToolMeta] = None  # 모든 분기에서 채워 반환

# ===== 유틸 =====
def _resolve_safe(path: str) -> Path:
    """ROOT_DIR 기준 상대경로를 안전하게 해석한다."""
    p = (ROOT_DIR / path).resolve()
    if ROOT_DIR not in p.parents and p != ROOT_DIR:
        raise ValueError(f"Path outside WORKDIR is not allowed: {p}")
    return p

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", "replace")).hexdigest()

def _read_text(p: Path, encoding="utf-8") -> str:
    return p.read_text(encoding=encoding)

def _write_text(p: Path, content: str, encoding="utf-8"):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding=encoding)

# ===== Args ======
class ReadFileArgs(BaseModel):
    """파일을 읽어 텍스트를 반환합니다."""
    # ❗ OpenAI function schema 대응: 모든 키는 required. 값이 선택이면 타입에 None 허용.
    path: str = Field(..., description="WORKDIR 기준 상대경로")
    start_line: Optional[int] = Field(..., ge=1, description="1-based 시작 줄 (없으면 null → 1로 처리)")
    end_line: Optional[int] = Field(..., ge=1, description="1-based 끝 줄(포함) (없으면 null → EOF)")
    with_line_numbers: bool = Field(..., description="줄번호 prefix 포함 여부(true/false)")

WriteMode = Literal["overwrite", "append", "insert_after_line", "replace_range"]

class WriteFileArgs(BaseModel):
    """파일을 씁니다."""
    # ❗ OpenAI function schema: properties의 모든 key가 required에 포함되어야 함.
    #    값이 선택적인 것은 타입에 | None 을 허용하고, 호출 시 키는 항상 보내되 값은 null 로 전달.
    path: str = Field(..., description="WORKDIR 기준 상대경로(없으면 생성)")
    mode: WriteMode = Field(..., description="overwrite, append, insert_after_line, replace_range 중 하나")
    content: str = Field(..., description="추가/치환할 텍스트")
    base_sha256: Optional[str] = Field(..., description="낙관적 락용 sha256 (없으면 null)")
    line: Optional[int] = Field(..., ge=1, description="insert_after_line 대상 줄 (없으면 null)")
    start_line: Optional[int] = Field(..., ge=1, description="replace_range 시작 줄 (없으면 null)")
    end_line: Optional[int] = Field(..., ge=1, description="replace_range 끝 줄 (없으면 null)")
    make_backup: bool = Field(..., description="적용 전에 .bak 생성 여부(true/false)")

    @model_validator(mode="after")
    def _validate_mode_fields(self):
        if self.mode == "insert_after_line" and not self.line:
            raise ValueError("insert_after_line 모드에는 'line'이 필요합니다.")
        if self.mode == "replace_range" and (not self.start_line or not self.end_line):
            raise ValueError("replace_range 모드에는 'start_line'과 'end_line'이 필요합니다.")
        return self

# ===== read_file =====
@tool(args_schema=ReadFileArgs)
def read_file(
    path: str,
    start_line: Optional[int],
    end_line: Optional[int],
    with_line_numbers: bool,
) -> ReadFileResult:
    """파일을 읽어 반환합니다."""
    try:
        p = _resolve_safe(path)
        meta = ToolMeta(function_name="read_file", parameters={"file_path": path})
        if not p.exists():
            return ReadFileResult(status="error", message=f"file not found: {path}", meta=meta)

        raw = _read_text(p)
        lines = raw.splitlines(keepends=False)
        total = len(lines)

        if total == 0:
            return ReadFileResult(
                status="ok",
                message="empty file",
                path=str(p.relative_to(ROOT_DIR)),
                total_lines=0,
                sha256=_sha256(raw),
                content="",
                meta=meta,
            )

        s = start_line or 1
        e = end_line or total
        s = max(1, min(total, s))
        e = max(s, min(total, e))

        sliced = lines[s - 1 : e]
        body = (
            "\n".join(f"{i + s}: {t}" for i, t in enumerate(sliced))
            if with_line_numbers else "\n".join(sliced)
        )

        return ReadFileResult(
            status="ok",
            message="success",
            path=str(p.relative_to(ROOT_DIR)),
            total_lines=total,
            sha256=_sha256(raw),
            content=body,
            meta=meta,
        )
    except Exception as e:
        return ReadFileResult(
            status="error",
            message=str(e),
            meta=ToolMeta(function_name="read_file", parameters={"file_path": path}),
        )

# ===== write_file (replace_lines 통합) =====
@tool(args_schema=WriteFileArgs)
def write_file(
    path: str,
    mode: WriteMode,
    content: str,
    base_sha256: Optional[str],
    line: Optional[int],
    start_line: Optional[int],
    end_line: Optional[int],
    make_backup: bool,
) -> WriteFileResult:
    """파일을 수정하거나 생성합니다."""
    try:
        p = _resolve_safe(path)
        meta = ToolMeta(function_name=f"write_file:{mode}", parameters={"file_path": path})
        old_text = _read_text(p) if p.exists() else ""
        old_sha = _sha256(old_text)

        # 낙관적 락 (옵션)
        if base_sha256 and p.exists() and base_sha256 != old_sha:
            return WriteFileResult(
                status="conflict",
                message="sha mismatch (file changed on disk)",
                path=str(p.relative_to(ROOT_DIR)),
                meta=meta,
            )

        new_text = old_text
        summaries: list[EditSummary] = []

        if mode == "overwrite":
            new_text = content
            summaries.append(
                EditSummary(
                    description="overwrite all",
                    affected_lines=list(range(1, content.count("\n") + 2)),
                )
            )

        elif mode == "append":
            new_text = old_text + content
            start_line_num = old_text.count("\n") + 1 if old_text else 1
            summaries.append(
                EditSummary(
                    description="append",
                    affected_lines=list(
                        range(start_line_num, start_line_num + content.count("\n") + 1)
                    ),
                )
            )

        elif mode == "insert_after_line":
            lines = old_text.splitlines(keepends=False)
            idx = max(1, min(len(lines), (line or 1))) - 1
            block = content.splitlines(keepends=False)
            lines[idx + 1 : idx + 1] = block
            new_text = "\n".join(lines) + (
                "\n" if (old_text.endswith("\n") or content.endswith("\n")) else ""
            )
            summaries.append(
                EditSummary(
                    description=f"insert_after_line {line}",
                    affected_lines=list(range((line or 0) + 1, (line or 0) + 1 + len(block))),
                )
            )

        elif mode == "replace_range":
            lines = old_text.splitlines(keepends=False)
            total = len(lines)
            s = max(1, min(total, (start_line or 1))) - 1
            e = max(1, min(total, (end_line or 1))) - 1  # inclusive
            repl = content.splitlines(keepends=False)
            lines[s : e + 1] = repl
            new_text = "\n".join(lines) + (
                "\n" if (old_text.endswith("\n") or content.endswith("\n")) else ""
            )
            summaries.append(
                EditSummary(
                    description=f"replace_range {start_line}-{end_line}",
                    affected_lines=list(range((start_line or 1), (end_line or 0) + 1)),
                )
            )

        else:
            return WriteFileResult(
                status="error",
                message=f"unsupported mode: {mode}",
                path=str(p.relative_to(ROOT_DIR)),
                meta=meta,
            )

        if new_text == old_text:
            return WriteFileResult(
                status="noop",
                message="no changes",
                path=str(p.relative_to(ROOT_DIR)),
                meta=meta,
            )

        if make_backup and p.exists():
            p.with_suffix(p.suffix + ".bak").write_text(old_text, encoding="utf-8")

        _write_text(p, new_text)
        new_sha = _sha256(new_text)

        udiff = "".join(
            difflib.unified_diff(
                old_text.splitlines(keepends=True),
                new_text.splitlines(keepends=True),
                fromfile=f"a/{p.name}",
                tofile=f"b/{p.name}",
                lineterm="\n",  # 표준 unified diff 포맷
            )
        )

        return WriteFileResult(
            status="ok",
            message="applied",
            path=str(p.relative_to(ROOT_DIR)),
            new_sha256=new_sha,
            diff_unified=udiff,
            summaries=summaries,
            meta=meta,
        )
    except Exception as e:
        return WriteFileResult(
            status="error",
            message=str(e),
            path=path,
            meta=ToolMeta(function_name=f"write_file:{mode}", parameters={"file_path": path}),
        )
