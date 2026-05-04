from __future__ import annotations

from collections.abc import Iterable

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text


def format_count(count: int, singular: str, plural: str | None = None) -> str:
    label = singular if count == 1 else plural or f"{singular}s"
    return f"{count:,} {label}"


def format_bytes(size: int) -> str:
    return format_count(size, "byte")


def print_file_table(
    console: Console,
    records: Iterable[object],
    *,
    title: str,
    path_attr: str = "relpath",
    size_attr: str = "size",
) -> None:
    table = Table(title=title, box=box.SIMPLE, show_lines=False)
    table.add_column("Path", overflow="fold")
    table.add_column("Size", justify="right")

    for record in records:
        table.add_row(
            Text(str(getattr(record, path_attr))),
            format_bytes(int(getattr(record, size_attr))),
        )

    console.print(table)


def print_skip_table(console: Console, entries: Iterable[dict[str, str]], *, title: str) -> None:
    table = Table(title=title, box=box.SIMPLE, show_lines=False)
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


def print_stats_table(
    console: Console,
    *,
    title: str,
    included_count: int,
    skipped_count: int,
    total_bytes: int,
    extension_counts: dict[str, int],
) -> None:
    console.print(f"[bold]{title}[/bold]")
    console.print(f"Included files: {included_count}")
    console.print(f"Skipped files:  {skipped_count}")
    console.print(f"Total bytes:    {total_bytes:,}")

    table = Table(title="By extension", box=box.SIMPLE, show_lines=False)
    table.add_column("Extension")
    table.add_column("Files", justify="right")

    for ext, count in sorted(extension_counts.items(), key=lambda item: -item[1]):
        table.add_row(ext or "(none)", str(count))

    console.print()
    console.print(table)
