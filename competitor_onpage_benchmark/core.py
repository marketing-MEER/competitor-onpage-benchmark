"""Benchmark one page against the pages that outrank it.

Fetches your URL and competitor URLs (e.g. the top 10 for a keyword), detects
each page's content format, measures on-page elements, and compares you with
the competitor median. Format comes first: Google already shows which format
it prefers for the query.
"""
import json
import re
import time
from collections import Counter
from pathlib import Path
from statistics import median
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

USER_AGENT = "competitor-onpage-benchmark/1.0 (+https://github.com/marketing-MEER/competitor-onpage-benchmark)"

NUMBERED_TITLE = re.compile(r"(^\d+\s)|\b\d+\s+(best|ways|tips|tools|examples|ideas|reasons|things|mistakes|"
                            r"steps|apps|alternatives|templates|strategies|questions)\b", re.I)
HOWTO_TITLE = re.compile(r"^how to\b|\bhow to\b.*\b(guide|step)|\b(tutorial|step[- ]by[- ]step|walkthrough)\b", re.I)
TOOL_WORDS = re.compile(r"\b(calculator|generator|checker|estimator|converter|tool|template builder)\b", re.I)
OPINION = re.compile(r"\b(i think|i believe|in my opinion|my take|why i|i've learned|unpopular opinion)\b", re.I)
STEP_HEADING = re.compile(r"^\s*(step\s*\d+|\d+[.)]\s)", re.I)
FILLER = {"the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "with", "your", "you", "how", "what", "why",
          "is", "are", "do", "does", "can", "it", "its", "this", "that", "faq", "faqs", "conclusion", "summary",
          "introduction", "step", "steps", "tip", "tips", "best", "top", "vs", "from", "by", "at", "be", "my", "our"}

NUMERIC = ["word_count", "h2_count", "h3_count", "images", "images_missing_alt", "internal_links", "external_links",
           "tables", "lists", "videos", "title_length", "meta_description_length"]
FLAGS = ["has_faq", "has_author", "has_date", "has_schema"]


def fetch(url: str, session) -> tuple[int, str, str]:
    """Download a page. A path to a saved .html file also works (handy for offline tests)."""
    if not url.startswith(("http://", "https://")) and Path(url).is_file():
        return 200, Path(url).resolve().as_uri(), Path(url).read_text(encoding="utf-8", errors="ignore")
    try:
        resp = session.get(url, timeout=25)
        return resp.status_code, resp.url, resp.text if "html" in resp.headers.get("Content-Type", "html") else ""
    except requests.RequestException as exc:
        return 0, url, f"<!-- {exc} -->"


def schema_types(soup) -> tuple[list[str], dict]:
    types, data = [], {}
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            payload = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        stack = payload if isinstance(payload, list) else [payload]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                t = item.get("@type")
                types += t if isinstance(t, list) else ([t] if t else [])
                for key in ("author", "datePublished", "dateModified"):
                    if key in item and key not in data:
                        data[key] = item[key]
                stack += [v for v in item.values() if isinstance(v, (dict, list))]
            elif isinstance(item, list):
                stack += item
    return sorted(set(map(str, types))), data


def detect_format(title: str, headings: list[str], soup, word_count: int, text: str) -> str:
    """List post, how-to guide, tool / calculator, video, opinion or article (in that order)."""
    forms = [f for f in soup.find_all("form")
             if f.find_all(["input", "select"], attrs={"type": lambda t: t not in ("hidden", "email", "submit",
                                                                                    "search", None)})]
    if forms and (TOOL_WORDS.search(title) or len(forms[0].find_all(["input", "select"])) >= 2):
        return "tool / calculator"
    has_video = soup.find("video") or soup.find("iframe", src=re.compile(r"youtube|vimeo|wistia", re.I))
    if has_video and word_count < 400:
        return "video"
    numbered = sum(1 for h in headings if re.match(r"^\s*\d+[.):\s]", h))
    if NUMBERED_TITLE.search(title) or numbered >= 5:
        return "list post"
    if HOWTO_TITLE.search(title) or sum(1 for h in headings if STEP_HEADING.match(h)) >= 3:
        return "how-to guide"
    words = max(word_count, 1)
    first_person = len(re.findall(r"\b(i|i'm|i've|my|me)\b", text.lower()))
    if OPINION.search(title) or OPINION.search(text[:1500]) or first_person / words > 0.015:
        return "opinion"
    return "article"


def analyze(url: str, status: int, final_url: str, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    host = urlparse(final_url).netloc
    title = soup.title.get_text(strip=True) if soup.title else ""
    meta = soup.find("meta", attrs={"name": lambda v: v and v.lower() == "description"})
    headings = {lvl: [h.get_text(" ", strip=True) for h in soup.find_all(lvl)] for lvl in ("h1", "h2", "h3")}
    types, ld = schema_types(soup)
    links = [urljoin(final_url, a["href"]) for a in soup.find_all("a", href=True)
             if not a["href"].startswith(("#", "mailto:", "tel:", "javascript:"))]
    internal = [l for l in links if urlparse(l).netloc == host]
    images = soup.find_all("img")
    author = (soup.find("meta", attrs={"name": "author"}) or soup.find(attrs={"rel": "author"})
              or soup.find(class_=re.compile(r"author|byline", re.I)) or ld.get("author"))
    date = (soup.find("meta", attrs={"property": re.compile(r"article:(published|modified)_time")})
            or soup.find("time") or ld.get("datePublished") or ld.get("dateModified"))
    faq = "FAQPage" in types or any(re.search(r"\b(faq|frequently asked)", h, re.I)
                                     for h in headings["h2"] + headings["h3"])
    videos = len(soup.find_all("video")) + len(soup.find_all("iframe", src=re.compile(r"youtube|vimeo|wistia", re.I)))
    tables = len(soup.find_all("table"))

    for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()
    body = soup.find("article") or soup.find("main") or soup.body or soup
    text = body.get_text(" ", strip=True)
    word_count = len(text.split())

    return {
        "url": url,
        "status": status,
        "format": detect_format(title, headings["h2"] + headings["h3"], BeautifulSoup(html, "html.parser"),
                                word_count, text) if status == 200 else "",
        "title": title,
        "title_length": len(title),
        "meta_description_length": len(meta.get("content", "")) if meta else 0,
        "h1": " | ".join(headings["h1"]),
        "h2_count": len(headings["h2"]),
        "h3_count": len(headings["h3"]),
        "word_count": word_count,
        "images": len(images),
        "images_missing_alt": sum(1 for i in images if not i.get("alt", "").strip()),
        "internal_links": len(internal),
        "external_links": len(links) - len(internal),
        "tables": tables,
        "lists": len(body.find_all(["ul", "ol"])),
        "videos": videos,
        "has_faq": bool(faq),
        "has_author": bool(author),
        "has_date": bool(date),
        "has_schema": bool(types),
        "schema_types": ", ".join(types),
        "_headings": headings["h2"] + headings["h3"],
        "_text": text.lower(),
    }


def collect(you: str, competitors: list[str], delay: float = 1.0, session=None) -> pd.DataFrame:
    session = session or requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    rows = []
    for i, url in enumerate([you, *competitors]):
        row = analyze(url, *fetch(url, session))
        row["page"] = "you" if i == 0 else f"competitor {i}"
        rows.append(row)
        if delay and i < len(competitors):
            time.sleep(delay)
    return pd.DataFrame(rows)


def format_check(pages: pd.DataFrame) -> dict:
    rivals = pages[(pages["page"] != "you") & (pages["status"] == 200)]
    counts = Counter(rivals["format"])
    dominant, n = counts.most_common(1)[0] if counts else ("-", 0)
    yours = pages.iloc[0]["format"]
    return {
        "your_format": yours,
        "dominant_format": dominant,
        "dominant_share_pct": round(n / max(len(rivals), 1) * 100),
        "format_mix": ", ".join(f"{k} {v}" for k, v in counts.most_common()),
        "match": yours == dominant,
    }


def compare(pages: pd.DataFrame) -> pd.DataFrame:
    """Your value vs competitor median for every metric, with a plain-language verdict."""
    rivals = pages[(pages["page"] != "you") & (pages["status"] == 200)]
    me = pages.iloc[0]
    rows = []
    for col in NUMERIC:
        med = median(rivals[col]) if len(rivals) else 0
        lo, hi = (rivals[col].min(), rivals[col].max()) if len(rivals) else (0, 0)
        mine = me[col]
        if col == "images_missing_alt":
            verdict = "fix" if mine > 0 else "ok"
        elif col in ("title_length", "meta_description_length"):
            verdict = "ok" if (col == "title_length" and 30 <= mine <= 60) or \
                              (col == "meta_description_length" and 70 <= mine <= 160) else "check length"
        elif med and mine < med * 0.7:
            verdict = "below competitors"
        elif med and mine > med * 1.5:
            verdict = "above competitors"
        else:
            verdict = "in range"
        rows.append({"metric": col, "you": mine, "competitor_median": med, "competitor_min": lo,
                     "competitor_max": hi, "verdict": verdict})
    for col in FLAGS:
        share = round(rivals[col].mean() * 100) if len(rivals) else 0
        mine = bool(me[col])
        verdict = "add it" if (not mine and share >= 50) else "ok"
        rows.append({"metric": col, "you": "yes" if mine else "no", "competitor_median": f"{share}% have it", "competitor_min": "",
                     "competitor_max": "", "verdict": verdict})
    return pd.DataFrame(rows)


def heading_gaps(pages: pd.DataFrame, min_pages: int = 2) -> pd.DataFrame:
    """Two-word phrases from competitor H2/H3s that 2+ competitors use and your page never mentions."""
    rivals = pages[(pages["page"] != "you") & (pages["status"] == 200)]
    my_text = pages.iloc[0]["_text"] + " " + " ".join(pages.iloc[0]["_headings"]).lower()
    seen = Counter()
    examples = {}
    for _, row in rivals.iterrows():
        phrases = set()
        for h in row["_headings"]:
            words = re.findall(r"[a-zäöüß0-9']+", h.lower())
            # only truly adjacent words form a phrase: a filler word or number breaks the chain
            for a, b in zip(words, words[1:]):
                if a in FILLER or b in FILLER or a.isdigit() or b.isdigit():
                    continue
                phrases.add(f"{a} {b}")
                examples.setdefault(f"{a} {b}", h)
        seen.update(phrases)
    rows = [{"phrase": p, "competitors_using": n, "example_heading": examples[p]}
            for p, n in seen.items() if n >= min_pages and p not in my_text]
    return pd.DataFrame(rows, columns=["phrase", "competitors_using", "example_heading"]).sort_values(
        ["competitors_using", "phrase"], ascending=[False, True])


def public_table(pages: pd.DataFrame) -> pd.DataFrame:
    cols = ["page", "url", "status", "format"] + NUMERIC + FLAGS + ["schema_types", "title", "h1"]
    return pages[cols]
