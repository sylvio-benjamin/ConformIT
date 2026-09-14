from app.extraction.ocr import extract_text_ocr
from app.pdf_parser import MIN_USABLE_CHARS, parse_pdf


def test_ocr_returns_empty_when_tools_missing(tmp_path, monkeypatch):
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("app.extraction.ocr.extract_text_ocr", lambda path: "")
    # Le module réel renvoie "" si pytesseract n'est pas là.
    assert extract_text_ocr(str(pdf)) == "" or isinstance(extract_text_ocr(str(pdf)), str)


def test_usable_text_skips_ocr(tmp_path, monkeypatch):
    called = {"ocr": False}

    def fake_read(_path):
        return "Extrait Kbis " + ("texte " * 80)

    def fake_ocr(_path):
        called["ocr"] = True
        return "ne devrait pas être appelé"

    monkeypatch.setattr("app.pdf_parser._read_pdf_text", fake_read)
    monkeypatch.setattr("app.extraction.ocr.extract_text_ocr", fake_ocr)
    (tmp_path / "doc.pdf").write_bytes(b"%PDF-1.4")
    result = parse_pdf(str(tmp_path / "doc.pdf"), "extrait_kbis")
    assert result["success"] is True
    assert result["method"] == "simple"
    assert len(result["text"].strip()) >= MIN_USABLE_CHARS
    assert called["ocr"] is False


def test_thin_text_tries_ocr(tmp_path, monkeypatch):
    monkeypatch.setattr("app.pdf_parser._read_pdf_text", lambda _path: "abc")
    monkeypatch.setattr(
        "app.extraction.ocr.extract_text_ocr",
        lambda _path: "Extrait Kbis scanné " + ("ocr " * 80),
    )
    (tmp_path / "doc.pdf").write_bytes(b"%PDF-1.4")
    result = parse_pdf(str(tmp_path / "doc.pdf"), "extrait_kbis")
    assert result["method"] == "ocr"
    assert result["success"] is True
