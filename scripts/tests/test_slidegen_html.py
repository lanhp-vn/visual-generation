from visgen.html_render import render_document

DOC = {
    "meta": {"lang": "en", "audience": "donors", "format": "deck-16x9",
             "title": "Cất Cánh (Takeoff) Fellowship Program"},
    "slides": [{"layout": "title", "content": {
        "title": "Cất Cánh (Takeoff) Fellowship Program",
        "subtitle_vi": "Bệ phóng cho trí tuệ Việt",
        "subtitle_en": "The launch pad for Viet talent",
        "footer": "Founded by Dr. Loi Nguyen & VISEMI Foundation"}}],
}


def test_renders_full_html_document():
    html = render_document(DOC)
    assert "<!doctype html>" in html.lower()
    assert 'class="deck"' in html          # html-ppt-compatible wrapper
    assert html.count('class="slide') == 1


def test_inlines_brand_css_and_font():
    html = render_document(DOC)
    assert "#001669" in html          # brand token present (inlined VISEMI theme)
    assert "Be Vietnam Pro" in html


def test_title_content_and_diacritics_present():
    html = render_document(DOC)
    assert "Cất Cánh (Takeoff) Fellowship Program" in html
    assert "Bệ phóng cho trí tuệ Việt" in html


def test_page_size_is_1920x1080():
    html = render_document(DOC)
    assert "1920px" in html and "1080px" in html
