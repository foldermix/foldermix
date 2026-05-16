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
    if console.is_terminal:
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
    else:
        # Print title as a plain line so it is never word-wrapped by the table
        # renderer, then render the table itself without a title.
        console.print(title)
        table = Table(box=None, show_header=True)
        table.add_column("Path", overflow="fold")
        table.add_column("Size", justify="right")

    for record in records:
        table.add_row(
            Text(str(getattr(record, path_attr))),
            format_size(int(getattr(record, size_attr))),
        )

    console.print(table)


def print_skip_table(console: Console, entries: Iterable[dict[str, str]], *, title: str) -> None:
    if console.is_terminal:
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
    else:
        console.print(title)
        table = Table(box=None, show_header=True)
        table.add_column("Path", overflow="fold")
        table.add_column("Reason code", no_wrap=True)
        table.add_column("Message", overflow="fold")

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
        f"{format_count(included_count, 'file')} would be included",
        f"{format_count(skipped_count, 'file')} skipped",
    ]
    if converter_missing_count is not None:
        parts.append(
            f"{format_count(converter_missing_count, 'additional file')} "
            "without a supported converter"
        )

    if not console.is_terminal:
        console.print(" • ".join(parts))
        return

    rich_parts = [
        f"[bold green]{format_count(included_count, 'file')}[/bold green] would be included",
        f"[bold yellow]{format_count(skipped_count, 'file')}[/bold yellow] skipped",
    ]
    if converter_missing_count is not None:
        rich_parts.append(
            f"[bold magenta]{format_count(converter_missing_count, 'additional file')}[/bold magenta] "
            "without a supported converter"
        )
    console.print(
        Panel(
            " • ".join(rich_parts),
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
        f"{format_count(included_count, 'file')} matched",
        f"{format_count(skipped_count, 'file')} skipped",
    ]
    if duplicate_skip_count:
        parts.append(f"{format_count(duplicate_skip_count, 'duplicate')} deduped")

    if not console.is_terminal:
        console.print(" • ".join(parts))
        return

    rich_parts = [
        f"[bold green]{format_count(included_count, 'file')}[/bold green] matched",
        f"[bold yellow]{format_count(skipped_count, 'file')}[/bold yellow] skipped",
    ]
    if duplicate_skip_count:
        rich_parts.append(
            f"[bold magenta]{format_count(duplicate_skip_count, 'duplicate')}[/bold magenta] "
            "deduped"
        )
    console.print(
        Panel(
            " • ".join(rich_parts),
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
    if not console.is_terminal:
        line = (
            f"Pack complete: {format_count(file_count, 'file')}, "
            f"{format_size(total_bytes)} -> {output_path}"
        )
        if report_path is not None:
            line += f" (report: {report_path})"
        if policy_finding_count is not None:
            line += f" (policy findings: {policy_finding_count})"
        # markup=False: don't interpret path chars as Rich tags
        # soft_wrap=True: never word-wrap — keeps the whole line intact for grep/pipes
        console.print(line, markup=False, soft_wrap=True)
        return

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
    if console.is_terminal:
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
    else:
        console.print(title)
        summary = Table(box=None, show_header=True)
        summary.add_column("Metric", no_wrap=True)
        summary.add_column("Value")

    summary.add_row("Included files", format_count(included_count, "file"))
    summary.add_row("Skipped files", format_count(skipped_count, "file"))
    summary.add_row("Total size", format_size(total_bytes))
    console.print(summary)

    if console.is_terminal:
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
    else:
        ext_table = Table(title="By extension", box=None, show_header=True)
        ext_table.add_column("Extension")
        ext_table.add_column("Files", justify="right")

    for ext, count in sorted(extension_counts.items(), key=lambda item: -item[1]):
        ext_table.add_row(ext or "(none)", str(count))

    console.print()
    console.print(ext_table)
