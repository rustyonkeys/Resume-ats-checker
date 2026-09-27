"""One-page OCR subprocess. Run via ocr_analysis, not as an API entry point."""

import contextlib
import json
import sys

import fitz


def main():
    request = json.load(sys.stdin)
    with contextlib.redirect_stdout(sys.stderr):
        with fitz.open(request["path"]) as doc:
            page = doc[request["page"]]
            textpage = page.get_textpage_ocr(language=request["language"], dpi=request["dpi"],
                                             full=request["full"], tessdata=request["tessdata"])
            data = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT, textpage=textpage)
    json.dump(data, sys.stdout, ensure_ascii=True)


if __name__ == "__main__":
    main()
