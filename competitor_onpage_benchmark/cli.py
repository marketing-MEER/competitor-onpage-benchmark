"""Command line entry point: `competitor-onpage-benchmark YOUR_URL COMPETITOR_URL [...]`."""
from pathlib import Path

import click

from . import __version__, core
from .benchmark import STAT
from .report import Report, write_excel


@click.command()
@click.argument("your_url")
@click.argument("competitor_urls", nargs=-1)
@click.option("--urls", "url_file", type=click.Path(exists=True),
              help="Text file with competitor URLs, one per line (e.g. the top 10 for your keyword).")
@click.option("--keyword", "-k", default="", help="The keyword these pages compete for (shown in the report).")
@click.option("--delay", default=1.0, show_default=True, help="Seconds between requests.")
@click.option("-o", "--output", default="onpage_benchmark", show_default=True,
              help="Report name; writes <name>.html and <name>.xlsx")
@click.version_option(__version__)
def main(your_url, competitor_urls, url_file, keyword, delay, output):
    """Benchmark YOUR_URL against the pages that outrank it.

    Built by Meer Hamza - linkedin.com/in/meerhamza-seo
    """
    rivals = list(competitor_urls)
    if url_file:
        rivals += [l.strip() for l in Path(url_file).read_text(encoding="utf-8").splitlines() if l.strip()]
    if not rivals:
        raise click.UsageError("give at least one competitor URL (or --urls file)")

    pages = core.collect(your_url, rivals, delay)
    fmt = core.format_check(pages)
    comp = core.compare(pages)
    gaps = core.heading_gaps(pages)
    to_fix = comp[comp["verdict"].isin(["below competitors", "add it", "fix", "check length"])]

    report = Report(title="On-page benchmark",
                    subtitle=(f'"{keyword}" · ' if keyword else "") + f"{your_url} vs {len(rivals)} pages",
                    tool="competitor-onpage-benchmark")
    report.add_cards([
        ("Your format", fmt["your_format"], "good" if fmt["match"] else "bad"),
        ("Competitors' main format", f'{fmt["dominant_format"]} ({fmt["dominant_share_pct"]}%)'),
        ("Metrics to improve", len(to_fix), "warn" if len(to_fix) else "good"),
        ("Subtopics you don't cover", len(gaps), "warn" if len(gaps) else "good"),
    ])
    report.add_benchmark(STAT, how_used="Step 1 checks your format against the format most competitors use. "
                                        "Only then compare depth: length, headings, media, FAQ and schema.")
    verdict = ("✅ Your format matches what ranks." if fmt["match"] else
               f'⚠️ Most competitors use "{fmt["dominant_format"]}" and your page is "{fmt["your_format"]}". '
               "Restructure the page before adding more content.")
    report.add_text("Step 1: format", [verdict, f'Format mix on the competitor pages: {fmt["format_mix"]}.'])
    report.add_table("Step 2: what to improve", to_fix, note="Metrics where you fall short of the competitor median.",
                     sheet="To improve")
    report.add_table("Subtopics competitors cover and you don't", gaps,
                     note="Two-word phrases from 2+ competitor headings that never appear on your page.",
                     sheet="Subtopic gaps")
    report.add_table("All metrics vs competitor median", comp, sheet="Comparison")
    report.add_table("Every page", core.public_table(pages), sheet="Pages")

    html_path = report.save_html(Path(output).with_suffix(".html"))
    xlsx_path = write_excel(report.sheets, Path(output).with_suffix(".xlsx"))
    click.secho(f"Report: {html_path}\nData:   {xlsx_path}", fg="green", bold=True)
    click.echo(verdict.encode("ascii", "ignore").decode().strip())  # Windows consoles can't print emoji
    click.echo(comp.to_string(index=False))


if __name__ == "__main__":
    main()
