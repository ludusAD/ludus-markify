from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Status(str, Enum):
    ok = "ok"
    error = "error"


@dataclass
class InputFile:
    name: str
    content: bytes


@dataclass
class ConversionResult:
    input_name: str
    status: Status
    markdown: str = ""
    error: str = ""


@dataclass
class ConversionJob:
    files: list[InputFile]
    output_dir: Path


@dataclass
class UserError(Exception):
    message: str
    filename: str = ""

    def __str__(self) -> str:
        prefix = f"{self.filename}: " if self.filename else ""
        return f"{prefix}{self.message}"
