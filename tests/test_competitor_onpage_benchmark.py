import tempfile
import unittest
from pathlib import Path

from click.testing import CliRunner

from competitor_onpage_benchmark import cli, core

EXAMPLES = Path(__file__).parent.parent / "examples"
COMPETITORS = [str(EXAMPLES / "pages" / f) for f in ["pipelinehq.html", "salesdeck.html", "crmguide.html",
                                                     "closeflow.html"]]
WORDS = " ".join(["word"] * 500)


def page(title, body):
    return core.analyze("u", 200, "https://site.com/u", f"<html><head><title>{title}</title></head><body>{body}</body></html>")


class FormatTest(unittest.TestCase):
    def test_list_post_from_title_or_numbered_headings(self):
        self.assertEqual(page("9 Best CRM Tools", f"<p>{WORDS}</p>")["format"], "list post")
        heads = "".join(f"<h2>{i}. Tool {i}</h2>" for i in range(1, 7))
        self.assertEqual(page("CRM tools we like", heads + f"<p>{WORDS}</p>")["format"], "list post")

    def test_how_to(self):
        self.assertEqual(page("How to Set Up a CRM", f"<p>{WORDS}</p>")["format"], "how-to guide")
        steps = "".join(f"<h2>Step {i}: do it</h2>" for i in range(1, 4))
        self.assertEqual(page("CRM setup", steps + f"<p>{WORDS}</p>")["format"], "how-to guide")

    def test_tool(self):
        form = '<form><input type="number" name="a"><input type="number" name="b"><button>Go</button></form>'
        self.assertEqual(page("CRM ROI Calculator", form + "<p>short</p>")["format"], "tool / calculator")
        newsletter = '<form><input type="email" name="e"><input type="submit"></form>'
        self.assertNotEqual(page("CRM news", newsletter + f"<p>{WORDS}</p>")["format"], "tool / calculator")

    def test_opinion_and_article(self):
        self.assertEqual(page("Why I stopped using CRMs", f"<p>{WORDS}</p>")["format"], "opinion")
        self.assertEqual(page("CRM market overview", f"<p>{WORDS}</p>")["format"], "article")


class MetricTest(unittest.TestCase):
    def test_metrics_and_schema(self):
        html = ('<html><head><title>T</title><meta name="description" content="hello">'
                '<script type="application/ld+json">{"@graph":[{"@type":"Article","datePublished":"2026-01-01",'
                '"author":{"@type":"Person","name":"A"}},{"@type":"FAQPage"}]}</script></head><body><article>'
                '<h2>A</h2><h3>B</h3><img src="x"><img src="y" alt="ok"><a href="/in">in</a>'
                '<a href="https://other.com">out</a><table></table><p>one two three</p></article></body></html>')
        row = core.analyze("u", 200, "https://site.com/u", html)
        self.assertEqual(row["schema_types"], "Article, FAQPage, Person")
        self.assertTrue(row["has_faq"] and row["has_author"] and row["has_date"])
        self.assertEqual((row["images"], row["images_missing_alt"]), (2, 1))
        self.assertEqual((row["internal_links"], row["external_links"]), (1, 1))
        self.assertEqual(row["tables"], 1)


class BenchmarkTest(unittest.TestCase):
    def setUp(self):
        self.pages = core.collect(str(EXAMPLES / "pages" / "your_page.html"), COMPETITORS, delay=0)

    def test_format_check(self):
        fmt = core.format_check(self.pages)
        self.assertEqual((fmt["your_format"], fmt["dominant_format"], fmt["match"]), ("article", "list post", False))
        self.assertEqual(fmt["dominant_share_pct"], 75)

    def test_compare_flags_gaps(self):
        comp = core.compare(self.pages).set_index("metric")
        self.assertEqual(comp.at["word_count", "verdict"], "below competitors")
        self.assertEqual(comp.at["has_schema", "verdict"], "add it")
        self.assertEqual(comp.at["images_missing_alt", "verdict"], "fix")

    def test_heading_gaps_use_adjacent_words_only(self):
        phrases = core.heading_gaps(self.pages)["phrase"].tolist()
        self.assertIn("crm pricing", phrases)
        self.assertIn("lead scoring", phrases)
        self.assertNotIn("crm small", phrases)   # "CRM for your small business": not adjacent


class CliTest(unittest.TestCase):
    def test_example_writes_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "bench"
            res = CliRunner().invoke(cli.main, [str(EXAMPLES / "pages" / "your_page.html"), *COMPETITORS,
                                                "--delay", "0", "-o", str(out)])
            self.assertEqual(res.exit_code, 0, res.output)
            self.assertIn("On-page benchmark", out.with_suffix(".html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
