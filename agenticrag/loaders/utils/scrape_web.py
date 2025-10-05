def scrape_web(url: str) -> dict | None:
    """Scrape and return Markdown content from a website using httpx + BeautifulSoup"""
    try:
        import httpx
        import bs4
        from markdownify import markdownify
    except ImportError:
        raise ImportError(
            "Required modules not found. Install them via:\n"
            "`pip install httpx beautifulsoup4 markdownify`"
        )

    headers = {"User-Agent": "Mozilla/5.0 (compatible; TextScraper/1.0)"}

    try:
        response = httpx.get(url, headers=headers, follow_redirects=True, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Request failed: {e}")
        return None

    soup = bs4.BeautifulSoup(response.text, "html.parser")

    title = soup.title.string.strip() if soup.title and soup.title.string else None
    site_name = title or url.split("//")[1].split("/")[0]

    body_html = soup.body.decode_contents() if soup.body else response.text
    markdown_content = markdownify(body_html)
    markdown_result = f"# {title}\n\n{markdown_content}" if title else markdown_content
    return {"site_name": site_name, "markdown": markdown_result}
