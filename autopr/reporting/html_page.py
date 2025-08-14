from __future__ import annotations

"""
Shared HTML page builder for simple reports.

Provides a minimal wrapper with a common header and basic styles.
"""

from dataclasses import dataclass

BASE_CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
.container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
.header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }
.content { padding: 30px; }
"""


@dataclass(frozen=True)
class PageHeader:
    title: str
    subtitle: str | None = None


def build_basic_page(*, header: PageHeader, generated_at: str | None, content_html: str, extra_css: str | None = None) -> str:
    css = BASE_CSS + (extra_css or "")
    subtitle_html = f"<p>{header.subtitle}</p>" if header.subtitle else ""
    generated_html = f"<p>Generated on {generated_at}</p>" if generated_at else ""
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>{header.title}</title>
    <style>
{css}
    </style>
</head>
<body>
    <div class=\"container\">
        <div class=\"header\">
            <h1>{header.title}</h1>
            {subtitle_html}
            {generated_html}
        </div>
        <div class=\"content\">
{content_html}
        </div>
    </div>
</body>
 </html>"""
