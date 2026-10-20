<div align="center">

# 📏 competitor-onpage-benchmark

### Put your page next to the pages that outrank it: format first, then depth.

[![tests](https://github.com/marketing-MEER/competitor-onpage-benchmark/actions/workflows/ci.yml/badge.svg)](https://github.com/marketing-MEER/competitor-onpage-benchmark/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![No API keys](https://img.shields.io/badge/API%20keys-none%20needed-brightgreen)
[![Part of SEO Toolbox](https://img.shields.io/badge/part%20of-SEO%20Toolbox-orange)](https://github.com/marketing-MEER/seo-toolbox)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Meer%20Hamza-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/meerhamza-seo)

[🚀 Quick start](#quick-start) · [⚙️ How it works](#how-it-works) · [📄 Report](#report) · [❓ FAQ](#faq) · [👤 Author](#author)

</div>

---

## 💡 What it does

When a page won't move past position 8, the usual answer is "add more words". Often the real problem is that the page is the wrong **kind** of page: an essay where Google ranks list posts, or a list where it ranks step-by-step guides.

`competitor-onpage-benchmark` takes your URL and the pages that outrank it. First it **detects every page's content format**. Then it compares your page with the competitor median on everything measurable, and lists the subtopics competitors cover in their headings that your page never mentions.

- ✅ Format detection: **list post**, **how-to guide**, **tool / calculator**, **video**, **opinion**, **article**
- ✅ 16 metrics vs competitor median: words, H2/H3, images, alt text, links, tables, lists, video, title/meta length, FAQ, author, date, schema
- ✅ Subtopic gaps from competitor headings
- ✅ Works on live URLs or saved `.html` files

## 📊 Why this matters

> **Content Types Most Likely To Rank On Page 1** · NP Digital, December 2024 (10,000 page-one results across industries)
> - List posts make up 32% of page-one results, the largest single format.
> - How-to guides account for 28% of top-ranking content.
> - Tools and calculators represent 18% of page-one URLs.
> - Opinion pieces appear in only 9% of page-one results.
>
> Data: [Neil Patel marketing stats](https://neilpatel.com/marketing-stats/content-types-ranking-page-one/)

**How competitor-onpage-benchmark uses this:** the study's advice is *"Audit page-one competitors by format, because Google already tells you what it prefers. Match the dominant format before trying to out-optimize on depth."* So the report puts the format check first and the depth comparison second.

<a id="quick-start"></a>

## 🚀 Quick start

```bash
git clone https://github.com/marketing-MEER/competitor-onpage-benchmark.git
cd competitor-onpage-benchmark
pip install -e .

# offline example with saved pages
competitor-onpage-benchmark examples/pages/your_page.html --urls examples/competitors.txt -k "crm for small business"

# live pages
competitor-onpage-benchmark https://yoursite.com/crm-guide https://rival.com/best-crm https://other.com/crm-tools
```

This writes **`onpage_benchmark.html`** (a formatted report) and **`onpage_benchmark.xlsx`** (all data).

> [!TIP]
> Google your keyword and paste the top 5–10 organic URLs into a text file, one per line, then pass it with `--urls`.

## 📥 Input

| Argument | What it is |
|---|---|
| `YOUR_URL` | Your page: a URL or a saved `.html` file |
| `COMPETITOR_URLS` | Any number of competitor URLs or `.html` files |
| `--urls file.txt` | Competitor URLs from a file, one per line |

<a id="how-it-works"></a>

## ⚙️ How it works

**1. Format detection** (checked in this order):

| Format | Detected when |
|---|---|
| 🧮 tool / calculator | The page has a form with real inputs (not just newsletter/search) and a tool word in the title or 2+ inputs |
| 🎬 video | An embedded video, and under 400 words of text |
| 📋 list post | A number in the title ("9 best…", "7 ways…") or 5+ numbered headings |
| 🪜 how-to guide | "How to…" / "step-by-step" / "tutorial" in the title, or 3+ "Step N" headings |
| 💬 opinion | Opinion phrases ("I think", "my take") or a high share of first-person words |
| 📄 article | Everything else |

**2. Depth comparison.** Main content only: nav, header, footer, sidebars and forms are removed before counting words.

| Verdict | Rule |
|---|---|
| below competitors | Your value is under 70% of the competitor median |
| above competitors | Over 150% of the median |
| add it | You lack a feature (FAQ, author, date, schema) that 50%+ of competitors have |
| fix | Images without alt text |
| check length | Title outside 30–60 or meta description outside 70–160 characters |

**3. Subtopic gaps**: two-word phrases that appear in the H2/H3 headings of 2+ competitors and nowhere on your page.

### Options

| Option | Default | What it does |
|---|---|---|
| `--urls` | – | File with competitor URLs |
| `--keyword`, `-k` | – | Shown in the report title |
| `--delay` | `1.0` | Seconds between requests |
| `-o`, `--output` | `onpage_benchmark` | Report name; writes `.html` and `.xlsx` |

<a id="report"></a>

## 📄 The report

| Section / Excel sheet | Shows |
|---|---|
| Summary cards | Your format, competitors' main format, metrics to improve, subtopic gaps |
| Step 1: format | Whether your format matches what ranks, and the format mix |
| **To improve** | Only the metrics where you fall short |
| **Subtopic gaps** | Phrases from competitor headings, with an example heading |
| **Comparison** | Every metric: you, competitor median, min, max, verdict |
| **Pages** | Every page with all metrics, schema types, title and H1 |

<details>
<summary>📄 Example: real output from <code>examples/</code> (fictional pages for "crm for small business")</summary>

**Step 1:** *Most competitors use "list post" and your page is "article". Restructure the page before adding more content.* Format mix: list post 3, how-to guide 1.

**Step 2: what to improve**

| metric | you | competitor median | verdict |
|---|---|---|---|
| word count | 485 | 1,661 | below competitors |
| h2 count | 3 | 10.5 | below competitors |
| images | 1 | 6 | below competitors |
| images missing alt | 1 | 0 | fix |
| tables | 0 | 1 | below competitors |
| has faq | no | 75% have it | add it |
| has author | no | 100% have it | add it |
| has schema | no | 100% have it | add it |

**Subtopics competitors cover and you don't** (top 6): crm pricing (4 competitors), lead scoring (3), mobile app (3), pipeline tracking (3), reporting dashboards (3), sales automation (3).

</details>

## 🧰 More free SEO tools

This repo is one tool in the **[SEO Toolbox](https://github.com/marketing-MEER/seo-toolbox)**, a family of free, single-purpose SEO tools. Related:
- [serp-competitor-finder](https://github.com/marketing-MEER/serp-competitor-finder): find which competitors to benchmark against
- [content-gap-crawler](https://github.com/marketing-MEER/content-gap-crawler): topic-level gaps across whole sites
- [seo-workhorse](https://github.com/marketing-MEER/seo-workhorse): audit, clustering, redirects and GSC quick wins in one CLI

<a id="faq"></a>

## ❓ FAQ

<details><summary><b>Is format detection always right?</b></summary>

It uses simple, readable rules (see the table above), so it can misread an unusual page. The "Pages" sheet shows the detected format for each URL. Check it before restructuring.
</details>

<details><summary><b>Some competitor pages show status 403 or 0.</b></summary>

Some sites block automated requests. Save the page from your browser (Ctrl+S → "Webpage, HTML only") and pass the `.html` file instead.
</details>

<details><summary><b>Should I just copy the competitor median?</b></summary>

No. The median shows what Google currently rewards for the query. Match the format and cover the missing subtopics, but write something better, not longer.
</details>

<details><summary><b>Is my data sent anywhere?</b></summary>

No. It only downloads the pages you list (with its own user agent and a delay between requests) and writes the report on your computer.
</details>

## 🧪 Tests

```bash
python -m unittest discover -s tests -t . -v
```

## 📄 License

[MIT](LICENSE). Free for personal and commercial use. Benchmark figures © their original publishers, quoted with a link to the source.

<a id="author"></a>

## 👤 Author

**Meer Hamza** · SEO Team Lead · Berlin 🇩🇪
10+ years in SEO, AEO and GEO. I build small tools that take the spreadsheet work out of SEO.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/meerhamza-seo)
[![Email](https://img.shields.io/badge/Email-meerhamza5%40gmail.com-D14836?logo=gmail&logoColor=white)](mailto:meerhamza5@gmail.com)

<div align="center">

**If this saved you time, a ⭐ helps other SEOs find it.**

</div>
