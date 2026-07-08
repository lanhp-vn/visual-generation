import sys; sys.path.insert(0, "scripts/lib")
from visgen.qr import qr_svg


def test_qr_svg_is_responsive_svg():
    svg = qr_svg("https://forms.gle/sGrc2sXojs4ZqydR6")
    assert svg.lstrip().startswith("<svg")
    assert "viewBox=" in svg and 'width="100%"' in svg
    assert "#001669" in svg
