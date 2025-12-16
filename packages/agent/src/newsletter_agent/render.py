from __future__ import annotations
from typing import List
from jinja2 import Environment, PackageLoader, select_autoescape
from markdown_it import MarkdownIt
import bleach
from markupsafe import Markup
from .types import Newsletter, SelectedItem

env = Environment(
    loader=PackageLoader("newsletter_agent", "prompts"),
    autoescape=select_autoescape(["html", "xml"])
)

_md = MarkdownIt("commonmark").enable("linkify")
_ALLOWED_TAGS = [
    "p", "strong", "em", "a", "ul", "ol", "li", "code", "pre", "blockquote", "br"
]
_ALLOWED_ATTRS = {"a": ["href", "title", "target", "rel"]}

def _md_filter(text: str | None) -> Markup:
    if not text:
        return Markup("")
    html = _md.render(text)
    safe = bleach.clean(html, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS, protocols=["http", "https"], strip=True)
    # Ensure external links open in new tab with noopener
    safe = safe.replace("<a ", "<a target=\"_blank\" rel=\"noopener noreferrer\" ")
    return Markup(safe)

env.filters["md"] = _md_filter

def render_newsletter(subject: str, items: List[SelectedItem]) -> Newsletter:
    tpl = env.get_template("newsletter.html.jinja")
    html = tpl.render(subject=subject, items=items)
    text_lines = [subject, ""]
    for i, it in enumerate(items, start=1):
        text_lines += [
            f"{i}. {it.title} ({it.source})",
            f"   {it.url}",
            f"   Why it matters: {it.why_it_matters}",
            f"   Summary: {it.summary}",
            ""
        ]
    return Newsletter(subject=subject, html=html, text="\n".join(text_lines).strip(), items=items)
