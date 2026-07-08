import sys; sys.path.insert(0, "scripts/lib")
from visgen.qr import qr_svg
from visgen.tokens import load_tokens


def test_qr_svg_is_responsive_svg():
    svg = qr_svg("https://forms.gle/sGrc2sXojs4ZqydR6")
    assert svg.lstrip().startswith("<svg")
    assert "viewBox=" in svg and 'width="100%"' in svg
    assert load_tokens()["themes"]["light"]["--navy"] in svg
