"""Export the editable draft DOCX to a real PDF with LibreOffice."""
from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import re


def main() -> None:
    root = Path.cwd()
    reports = root / "reports"
    facts = json.loads((root / "outputs" / "report_facts.json").read_text(encoding="utf-8"))
    nrp = facts.get("identity", {}).get("nrp", "NRP")
    stem = f"{nrp}_ETS_Tekber_Gasal26-27_DRAFT"
    docx = reports / f"{stem}.docx"
    pdf = reports / f"{stem}.pdf"
    if not docx.is_file():
        raise FileNotFoundError(docx)
    soffice = shutil.which("soffice")
    if not soffice:
        raise RuntimeError("LibreOffice 'soffice' tidak ditemukan di PATH.")
    with tempfile.TemporaryDirectory(prefix="pdf_export_", dir=reports) as temp:
        result = subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", temp, str(docx)],
            check=True, capture_output=True, text=True,
        )
        created = Path(temp) / (docx.stem + ".pdf")
        if not created.is_file():
            raise RuntimeError(f"LibreOffice tidak membuat PDF. {result.stdout} {result.stderr}")
        shutil.copy2(created, pdf)
    pdfinfo = shutil.which("pdfinfo")
    if not pdfinfo:
        raise RuntimeError("Perintah 'pdfinfo' tidak ditemukan untuk memeriksa PDF.")
    info = subprocess.run([pdfinfo, str(pdf)], check=True, capture_output=True, text=True).stdout
    match = re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE)
    if not match or int(match.group(1)) < 10:
        raise RuntimeError("PDF tidak terbaca atau memiliki halaman terlalu sedikit.")
    print(f"{pdf} | {match.group(1)} halaman | {pdf.stat().st_size} byte")


if __name__ == "__main__":
    main()
