#!/usr/bin/env python3
"""
End-to-end tests for the built site in dist/ (Astro pages with the Sphinx labs merged in).

Run after `task build`:  uv run pytest -n0 tests/test_site.py
"""

import http.server
import pathlib
import socketserver
import threading
from collections.abc import Iterator

import pytest
from playwright.sync_api import Page, expect, sync_playwright

DIST = pathlib.Path(__file__).resolve().parents[1] / "dist"
SPHINX_LABS = ["container-security-101", "container-security-201", "policy-as-code"]


@pytest.fixture(scope="module")
def base_url() -> Iterator[str]:
    """Serve dist/ over HTTP so root-relative asset paths resolve like they do on GitHub Pages"""

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(DIST), **kwargs)

        def log_message(self, *args):
            pass

    with socketserver.TCPServer(("127.0.0.1", 0), Handler) as server:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        yield f"http://127.0.0.1:{server.server_address[1]}"
        server.shutdown()


@pytest.fixture(scope="module")
def page() -> Iterator[Page]:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        yield browser.new_page()
        browser.close()


def test_sphinx_labs_ship_alongside_the_astro_pages() -> None:
    """The merge keeps Astro's top-level pages but must not drop the labs' own index"""
    assert 'id="labs"' in (DIST / "index.html").read_text(), (
        "the home page should be Astro's, not Sphinx's"
    )
    assert (DIST / "labs" / "index.html").is_file(), (
        "the Sphinx labs index should ship at /labs/"
    )
    for lab in SPHINX_LABS:
        assert (DIST / "labs" / f"{lab}.html").is_file(), (
            f"{lab} should ship at /labs/{lab}.html"
        )


def test_home_canonical_is_the_root_url() -> None:
    assert '<link rel="canonical" href="https://jonzeolla.com/">' in (
        DIST / "index.html"
    ).read_text(), "Google picks / for the home page, so the canonical must match"


def test_sphinx_sources_are_not_published() -> None:
    # Sphinx still creates an empty _sources/, so check for files rather than the directory.
    assert not list((DIST / "_sources").rglob("*.txt")), (
        "raw sources get crawled as thin pages"
    )


def test_sitemap_lists_llms_txt_and_every_lab() -> None:
    sitemap = (DIST / "sitemap.xml").read_text()
    assert "<loc>https://jonzeolla.com/llms.txt</loc>" in sitemap
    labs = list((DIST.parent / "docs" / "labs").glob("*.md"))
    assert labs, "the sitemap reads docs/labs/*.md, so this path must keep matching"
    for lab in labs:
        url = f"https://jonzeolla.com/labs/{lab.stem}.html"
        assert f"<loc>{url}</loc>" in sitemap, f"{url} should be in the sitemap"
    assert "Sitemap: https://jonzeolla.com/sitemap.xml" in (
        DIST / "robots.txt"
    ).read_text(), "robots.txt is how Google finds the sitemap"


def test_labs_index_lists_every_lab(base_url: str, page: Page) -> None:
    page.goto(f"{base_url}/labs/")
    for lab in SPHINX_LABS:
        expect(page.locator(f'a[href="{lab}.html"]').first).to_be_visible()


def test_lab_modules_start_collapsed_and_toggle(base_url: str, page: Page) -> None:
    page.goto(f"{base_url}/")
    buttons = page.locator("#labs button.agenda")
    lists = page.locator("#labs ul")
    assert buttons.count() == lists.count() > 0

    for i in range(lists.count()):
        expect(lists.nth(i)).to_be_hidden()
        expect(buttons.nth(i)).to_have_attribute("aria-expanded", "false")

    buttons.first.click()
    expect(lists.first).to_be_visible()
    expect(buttons.first).to_have_attribute("aria-expanded", "true")
    expect(buttons.first.locator("span")).to_have_text("−")
    expect(lists.nth(1)).to_be_hidden()

    buttons.first.click()
    expect(lists.first).to_be_hidden()
    expect(buttons.first).to_have_attribute("aria-expanded", "false")
    expect(buttons.first.locator("span")).to_have_text("+")
