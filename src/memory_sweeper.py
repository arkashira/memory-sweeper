"""memory_sweeper – simple static analysis for resource leaks."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import List, Set, Tuple, Optional


@dataclass(frozen=True)
class LeakReport:
    """A single leak detection report."""
    line: int
    severity: str  # "low", "medium", "high"
    message: str
    suggestion: str


class _LeakVisitor(ast.NodeVisitor):
    """AST visitor that collects open/socket calls and close calls."""

    def __init__(self) -> None:
        super().__init__()
        # (node, var_name, line)
        self.open_calls: List[Tuple[ast.Call, Optional[str], int]] = []
        # (node, var_name, line)
        self.socket_calls: List[Tuple[ast.Call, Optional[str], int]] = []
        # set of variable names that have a .close() call
        self.closed_vars: Set[str] = set()
        # set of (line) that are safe because they appear in a with statement
        self.with_safe_lines: Set[int] = set()

    def visit_With(self, node: ast.With) -> None:
        """Mark any resource opened inside a with‑statement as safe."""
        for item in node.items:
            expr = item.context_expr
            if isinstance(expr, ast.Call):
                func = expr.func
                if isinstance(func, ast.Name) and func.id == "open":
                    self.with_safe_lines.add(expr.lineno)
                elif (
                    isinstance(func, ast.Attribute)
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "socket"
                    and func.attr == "socket"
                ):
                    self.with_safe_lines.add(expr.lineno)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Capture assignments of open()/socket() to a variable."""
        if isinstance(node.value, ast.Call):
            func = node.value.func
            var_name = None
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                var_name = node.targets[0].id
            if isinstance(func, ast.Name) and func.id == "open":
                self.open_calls.append((node.value, var_name, node.lineno))
            elif (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "socket"
                and func.attr == "socket"
            ):
                self.socket_calls.append((node.value, var_name, node.lineno))
        self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr) -> None:
        """Capture calls like open() used directly (no assignment)."""
        if isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Name) and func.id == "open":
                self.open_calls.append((node.value, None, node.lineno))
            elif (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "socket"
                and func.attr == "socket"
            ):
                self.socket_calls.append((node.value, None, node.lineno))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Capture .close() calls on variables."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "close" and isinstance(node.func.value, ast.Name):
                self.closed_vars.add(node.func.value.id)
        self.generic_visit(node)


def _is_safe(call_line: int, safe_lines: Set[int]) -> bool:
    """Return True if the call appears inside a with‑statement."""
    return call_line in safe_lines


def detect_leaks(source: str) -> List[LeakReport]:
    """
    Detect resource leaks in the given Python source code.

    Currently supports:
    * ``open`` – file handles (severity: high)
    * ``socket.socket`` – sockets (severity: medium)

    A resource is considered safe when:
    * It is used inside a ``with`` statement, or
    * The variable it was assigned to is later closed via ``.close()``.
    """
    tree = ast.parse(source)
    visitor = _LeakVisitor()
    visitor.visit(tree)

    reports: List[LeakReport] = []

    # Helper to create a report
    def make_report(line: int, severity: str, message: str, suggestion: str) -> LeakReport:
        return LeakReport(line=line, severity=severity, message=message, suggestion=suggestion)

    # Process open() calls
    for call, var_name, line in visitor.open_calls:
        if _is_safe(line, visitor.with_safe_lines):
            continue
        if var_name and var_name in visitor.closed_vars:
            continue
        suggestion = (
            "Wrap the file operation in a with‑statement:\n"
            "with open('path') as f:\n"
            "    # use f here"
        )
        reports.append(
            make_report(
                line=line,
                severity="high",
                message="File opened without guaranteed close.",
                suggestion=suggestion,
            )
        )

    # Process socket.socket() calls
    for call, var_name, line in visitor.socket_calls:
        if _is_safe(line, visitor.with_safe_lines):
            continue
        if var_name and var_name in visitor.closed_vars:
            continue
        suggestion = (
            "Use a context manager or ensure the socket is closed:\n"
            "with socket.socket() as s:\n"
            "    # use s here"
        )
        reports.append(
            make_report(
                line=line,
                severity="medium",
                message="Socket created without guaranteed close.",
                suggestion=suggestion,
            )
        )

    # Sort by line number for deterministic output
    reports.sort(key=lambda r: r.line)
    return reports
