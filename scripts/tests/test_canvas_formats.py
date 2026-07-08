"""The generalization test: the same engine renders non-slide stage sizes."""
from visgen.canvas import render_canvas
from visgen.pngsize import png_size

def test_square_format_renders_1080x1080(tmp_path):
    doc = {"meta": {"format": "square", "theme": "light", "title": "t"},
           "pages": [{"layout": "quote", "content": {"quote": "Cất Cánh"}}]}
    report = render_canvas(doc, tmp_path / "sq", fmt="png")
    assert report["page_px"] == [1080, 1080]
    assert png_size(tmp_path / "sq/png/page-01.png") == (1080, 1080)
