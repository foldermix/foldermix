from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def format_count(count: int, singular: str, plural: str | None = None) -> str:
    label = singular if count == 1 else plural or f"{singular}s"
    return f"{count:,} {label}"


def format_bytes(size: int) -> str:
    return format_count(size, "byte")


def format_size(size: int) -> str:
    """Human-readable file size: B / KB / MB / GB."""
    for unit, threshold in (("GB", 1 << 30), ("MB", 1 << 20), ("KB", 1 << 10)):
        if size >= threshold:
            return f"{size / threshold:.1f} {unit}"
    return format_bytes(size)


def print_file_table(
    console: Console,
    records: Iterable[object],
    *,
    title: str,
    path_attr: str = "relpath",
    size_attr: str = "size",
) -> None:
    table = Table(
        title=title,
        title_style="bold cyan",
        box=box.ROUNDED,
        border_style="bright_black",
        header_style="bold white on dark_green",
        row_styles=["none", "dim"],
        show_lines=False,
    )
    table.add_column("Path", overflow="fold", style="bright_white")
    table.add_column("Size", justify="right", style="green")

    for record in records:
        table.add_row(
            Text(str(getattr(record, path_attr))),
            format_size(int(getattr(record, size_attr))),
        )

    console.print(table)


def print_skip_table(console: Console, entries: Iterable[dict[str, str]], *, title: str) -> None:
    table = Table(
        title=title,
        title_style="bold yellow",
        box=box.ROUNDED,
        border_style="bright_black",
        header_style="bold white on dark_red",
        row_styles=["none", "dim"],
        show_lines=False,
    )
    table.add_column("Path", overflow="fold", style="bright_white")
    table.add_column("Reason code", no_wrap=True, style="yellow")
    table.add_column("Message", overflow="fold", style="white")

    for entry in entries:
        table.add_row(
            Text(entry["path"]),
            Text(entry["reason_code"]),
            Text(entry["message"]),
        )

    console.print(table)


def print_preview_summary(
    console: Console,
    *,
    included_count: int,
    skipped_count: int,
    converter_missing_count: int | None = None,
) -> None:
    parts = [
        f"[bold green]{format_count(included_count, 'file')}[/bold green] would be included",
        f"[bold yellow]{format_count(skipped_count, 'file')}[/bold yellow] skipped",
    ]
    if converter_missing_count is not None:
        parts.append(
            f"[bold magenta]{format_count(converter_missing_count, 'additional file')}[/bold magenta] "
            "without a supported converter"
        )
    console.print(
        Panel(
            " • ".join(parts),
            title="[bold cyan]Preview summary[/bold cyan]",
            border_style="cyan",
            padding=(0, 1),
        )
    )


def print_pack_scan_summary(
    console: Console,
    *,
    included_count: int,
    skipped_count: int,
    duplicate_skip_count: int = 0,
) -> None:
    parts = [
        f"[bold green]{format_count(included_count, 'file')}[/bold green] matched",
        f"[bold yellow]{format_count(skipped_count, 'file')}[/bold yellow] skipped",
    ]
    if duplicate_skip_count:
        parts.append(
            f"[bold magenta]{format_count(duplicate_skip_count, 'duplicate')}[/bold magenta] "
            "deduped"
        )
    console.print(
        Panel(
            " • ".join(parts),
            title="[bold cyan]Scan summary[/bold cyan]",
            border_style="bright_black",
            padding=(0, 1),
        )
    )


def print_pack_result(
    console: Console,
    *,
    output_path: Path | str,
    file_count: int,
    skipped_count: int,
    total_bytes: int,
    report_path: Path | str | None = None,
    policy_finding_count: int | None = None,
) -> None:
    table = Table(
        title="✅ Pack complete",
        title_style="bold green",
        box=box.ROUNDED,
        border_style="green",
        header_style="bold white on dark_green",
        show_lines=False,
    )
    table.add_column("Field", style="bold cyan", no_wrap=True)
    table.add_column("Value", style="white", overflow="fold")
    table.add_row("Output", str(output_path))
    table.add_row("Packed files", format_count(file_count, "file"))
    table.add_row("Skipped files", format_count(skipped_count, "file"))
    table.add_row("Output size", format_size(total_bytes))
    if report_path is not None:
        table.add_row("Report", str(report_path))
    if policy_finding_count is not None:
        table.add_row("Policy findings", str(policy_finding_count))

    console.print(table)


def print_stats_table(
    console: Console,
    *,
    title: str,
    included_count: int,
    skipped_count: int,
    total_bytes: int,
    extension_counts: dict[str, int],
) -> None:
    summary = Table(
        title=title,
        title_style="bold cyan",
        box=box.ROUNDED,
        border_style="bright_black",
        header_style="bold white on dark_green",
        show_lines=False,
    )
    summary.add_column("Metric", style="bold cyan", no_wrap=True)
    summary.add_column("Value", style="white")
    summary.add_row("Included files", format_count(included_count, "file"))
    summary.add_row("Skipped files", format_count(skipped_count, "file"))
    summary.add_row("Total size", format_size(total_bytes))
    console.print(summary)

    ext_table = Table(
        title="By extension",
        title_style="bold cyan",
        box=box.ROUNDED,
        border_style="bright_black",
        header_style="bold white on dark_green",
        show_lines=False,
    )
    ext_table.add_column("Extension", style="bright_white")
    ext_table.add_column("Files", justify="right", style="green")

    for ext, count in sorted(extension_counts.items(), key=lambda item: -item[1]):
        ext_table.add_row(ext or "(none)", str(count))

    console.print()
    console.print(ext_table)
