from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

PAGES = {
    "01_resumo_executivo.png": "resumo",
    "02_vendas.png": "vendas",
    "03_categorias.png": "categorias",
    "04_analise_economica.png": "economia",
    "05_aprendizado_de_maquina.png": "ml",
    "06_anomalias.png": "anomalias",
    "07_observabilidade.png": "observabilidade",
    "08_catalogo.png": "catalogo",
}


def main() -> None:
    output_dir = Path("docs") / "linkedin_screenshots"
    output_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1100}, device_scale_factor=1)
        for filename, page_key in PAGES.items():
            page.goto(f"http://127.0.0.1:8501/?page={page_key}", wait_until="networkidle")
            page.wait_for_selector(".stMainBlockContainer", timeout=15000)
            page.wait_for_timeout(8000)
            page.screenshot(path=output_dir / filename, full_page=True)
        browser.close()

    print(f"Saved {len(PAGES)} screenshots to {output_dir}")


if __name__ == "__main__":
    main()
