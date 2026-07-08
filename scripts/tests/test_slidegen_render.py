import json

from visgen.canvas import render_canvas

DOC = {
    "meta": {"lang": "en", "audience": "donors", "format": "deck-16x9", "title": "T"},
    "pages": [{"layout": "title", "content": {
        "title": "Cất Cánh", "subtitle_vi": "a", "subtitle_en": "b", "footer": "f"}}],
}


def test_png_size_reader(tmp_path):
    # 1x1 PNG
    import base64
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
    p = tmp_path / "x.png"
    p.write_bytes(png)
    from visgen.pngsize import png_size
    assert png_size(p) == (1, 1)


def test_render_produces_png_pdf_report(tmp_path):
    out = tmp_path / "out"
    report = render_canvas(DOC, out, fmt="both")

    from visgen.pngsize import png_size
    png = out / "png" / "page-01.png"
    assert png.is_file()
    assert png_size(png) == (1920, 1080)
    assert list((out / "pdf").glob("*.pdf"))
    on_disk = json.loads((out / "render_report.json").read_text(encoding="utf-8"))
    assert on_disk == report
    assert report["page_px"] == [1920, 1080]
    assert all(p["overflow"] is False for p in report["pages"])
