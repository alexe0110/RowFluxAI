from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table


class ProgressTracker:
    def __init__(self, total: int, console: Console | None = None):
        """
        Initialize progress tracker.

        Args:
            total: Total number of records to process.
            console: Rich console instance.
        """
        self.total = total
        self.console = console or Console()
        self.successful = 0
        self.failed = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self._progress: Progress | None = None
        self._task_id = None

    def start(self) -> None:
        """Start progress tracking."""
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            MofNCompleteColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            refresh_per_second=2,
        )
        self._progress.start()
        self._task_id = self._progress.add_task("Processing", total=self.total)

    def update(self, success: bool, tokens: int = 0, cost: float = 0.0) -> None:
        """
        Update progress after processing a record.

        Args:
            success: Whether processing was successful.
            tokens: Tokens used.
            cost: Cost incurred.
        """
        if success:
            self.successful += 1
        else:
            self.failed += 1

        self.total_tokens += tokens
        self.total_cost += cost

        if self._progress and self._task_id is not None:
            self._progress.update(
                self._task_id,
                advance=1,
                description=f"Processing (OK: {self.successful}, ERR: {self.failed})",
            )

    def stop(self) -> None:
        """Stop progress tracking."""
        if self._progress:
            self._progress.stop()

    def print_summary(self, duration_seconds: float) -> None:
        """
        Print final summary.

        Args:
            duration_seconds: Total duration in seconds.
        """
        minutes, seconds = divmod(int(duration_seconds), 60)
        hours, minutes = divmod(minutes, 60)

        if hours > 0:
            duration_str = f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            duration_str = f"{minutes}m {seconds}s"
        else:
            duration_str = f"{seconds}s"

        table = Table(title="Pipeline Summary", show_header=False, box=None)
        table.add_column("Metric", style="bold")
        table.add_column("Value", style="cyan")

        table.add_row("Total records", str(self.total))
        table.add_row("Successful", f"[green]{self.successful}[/green]")
        table.add_row(
            "Failed",
            f"[red]{self.failed}[/red]" if self.failed > 0 else str(self.failed),
        )
        table.add_row("Total tokens", f"{self.total_tokens:,}")
        table.add_row("Estimated cost", f"${self.total_cost:.4f}")
        table.add_row("Duration", duration_str)

        self.console.print()
        self.console.print(table)

    def __enter__(self) -> ProgressTracker:
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()
