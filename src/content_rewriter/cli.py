"""Typer CLI entry point for content-rewriter."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import typer
from rich.console import Console

from content_rewriter.llm import LLMClient, LLMError
from content_rewriter.models import ExtractorOutput, RewriteStatus
from content_rewriter.rewriter import rewrite_content
from content_rewriter.voice import load_voice_profile

app = typer.Typer(help="Bidirectional platform content transformer.")
console = Console()


@app.command("rewrite")
def rewrite_command(
    content_path: Path = typer.Argument(..., help="Path to content directory with extractor_output.json"),
    from_platform: str = typer.Option(..., "--from", "-f", help="Source platform (e.g. douyin)"),
    to_platforms: str = typer.Option(..., "--to", "-t", help="Target platform(s), comma-separated (e.g. xiaohongshu,wechat)"),
    output_dir: Path = typer.Option(Path("output"), "--output-dir", "-o", help="Output directory for drafts"),
    voice_config_dir: Path = typer.Option(Path.home() / ".content-rewriter", "--voice-dir", help="Voice profile directory"),
) -> None:
    """Rewrite extracted content for target platform(s)."""
    if not content_path.exists():
        console.print(f"[red]Error: Content path not found: {content_path}[/red]")
        raise typer.Exit(code=1)

    extractor_file = content_path / "extractor_output.json"
    if not extractor_file.exists():
        console.print(f"[red]Error: extractor_output.json not found in {content_path}[/red]")
        raise typer.Exit(code=1)

    try:
        raw = json.loads(extractor_file.read_text())
        source = ExtractorOutput.model_validate(raw)
    except Exception as e:
        console.print(f"[red]Error: Invalid extractor output: {e}[/red]")
        raise typer.Exit(code=1)

    voice_profile = load_voice_profile(config_dir=voice_config_dir)
    if voice_profile is None:
        console.print("[yellow]Warning: No voice profile found. Output will use generic style.[/yellow]")

    try:
        llm_client = LLMClient()
    except LLMError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)

    targets = [t.strip() for t in to_platforms.split(",")]

    console.print(f"[bold]Rewriting {source.content_id} from {from_platform} to {', '.join(targets)}...[/bold]")
    results = rewrite_content(
        source=source,
        from_platform=from_platform,
        to_platforms=targets,
        llm_client=llm_client,
        voice_profile=voice_profile,
    )

    today = date.today().isoformat()
    for result in results:
        draft_dir = output_dir / source.content_id
        draft_dir.mkdir(parents=True, exist_ok=True)
        draft_file = draft_dir / f"{result.target_platform}_draft.md"

        if result.status == RewriteStatus.FAILED:
            content = f"[REWRITE_FAILED]\n\nError: {result.error_message}\n\n---\n\nRaw transcript:\n{result.body}"
        elif voice_profile is None:
            content = f"[NO_VOICE_PROFILE]\n\n# {result.title}\n\n{result.body}"
            if result.hashtags:
                content += "\n\n" + " ".join(f"#{tag}" for tag in result.hashtags)
        else:
            content = f"# {result.title}\n\n{result.body}"
            if result.hashtags:
                content += "\n\n" + " ".join(f"#{tag}" for tag in result.hashtags)

        if result.cover_brief:
            content += f"\n\n---\n封面图建议: {result.cover_brief}"

        draft_file.write_text(content)
        status_icon = "✓" if result.status == RewriteStatus.SUCCESS else "✗"
        console.print(f"  {status_icon} {result.target_platform} → {draft_file}")

    failed = sum(1 for r in results if r.status == RewriteStatus.FAILED)
    if failed:
        console.print(f"\n[yellow]{failed}/{len(results)} rewrites failed[/yellow]")
        raise typer.Exit(code=1)
    else:
        console.print(f"\n[green]Done! {len(results)} draft(s) written.[/green]")


@app.command("feedback")
def feedback_command(
    action: str = typer.Argument(..., help="Action: accept or reject"),
    draft_path: Path = typer.Argument(..., help="Path to the draft file"),
    content_id: str = typer.Option(..., "--content-id", help="Content ID"),
    platform: str = typer.Option(..., "--platform", help="Target platform"),
    feedback_dir: Path = typer.Option(
        Path.home() / ".content-rewriter", "--feedback-dir", help="Feedback log directory"
    ),
) -> None:
    """Record feedback (accept/reject) for a rewrite draft."""
    if action not in ("accept", "reject"):
        console.print(f"[red]Error: action must be 'accept' or 'reject', got '{action}'[/red]")
        raise typer.Exit(code=1)

    feedback_dir.mkdir(parents=True, exist_ok=True)
    log_file = feedback_dir / "feedback.jsonl"

    entry = {
        "draft_path": str(draft_path),
        "platform": platform,
        "content_id": content_id,
        "timestamp": datetime.now().isoformat(),
        "action": action,
    }

    with log_file.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    icon = "✓" if action == "accept" else "✗"
    console.print(f"  {icon} Recorded {action} for {content_id} ({platform})")
