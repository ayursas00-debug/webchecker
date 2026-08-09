"""
check_once.py -- standalone single-run version for Kiro AI to execute.

Checks https://broneering.mfa.ee/ for whether "Applying for a long-term
visa (D - visa)" appears as a service option for the Embassy of the
Republic of Estonia in Abu Dhabi. Prints a JSON result and exits.

Setup (run once):
    pip install playwright
    playwright install chromium

Run:
    python check_once.py
"""

import json
from playwright.sync_api import sync_playwright

URL = "https://broneering.mfa.ee/en/"
TARGET_OFFICE_TEXT = "New Delhi"
# Check for either "D-visa" or "long stay" (case-insensitive)
TARGET_SERVICE_KEYWORDS = ["d-visa", "long stay"]

def check_once():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=30000)

        office_select = page.locator("select").first
        office_select.wait_for(state="visible", timeout=15000)
        options = office_select.locator("option").all_text_contents()

        match_index = None
        matched_text = None
        for i, text in enumerate(options):
            if TARGET_OFFICE_TEXT.lower() in text.lower():
                match_index = i
                matched_text = text.strip()
                break

        if match_index is None:
            browser.close()
            return {
                "found": False,
                "error": f"no office option matched '{TARGET_OFFICE_TEXT}'",
                "all_office_options": [o.strip() for o in options],
            }

        office_select.select_option(index=match_index)
        page.wait_for_timeout(5000)  # let the service list load after selecting the office

        service_texts = []
        found = False
        try:
            service_select = page.locator("select").nth(1)
            if service_select.count() > 0:
                service_texts = [o.strip() for o in service_select.locator("option").all_text_contents()]
                # Check if any keyword is found in any service option (case-insensitive)
                for service in service_texts:
                    service_lower = service.lower()
                    if any(keyword in service_lower for keyword in TARGET_SERVICE_KEYWORDS):
                        found = True
                        break
        except Exception:
            pass

        if not found:
            body_text = page.inner_text("body").lower()
            found = any(keyword in body_text for keyword in TARGET_SERVICE_KEYWORDS)

        browser.close()

        return {
            "found": found,
            "matched_office": matched_text,
            "service_options_seen": service_texts,
        }

if __name__ == "__main__":
    try:
        result = check_once()
    except Exception as e:
        result = {"found": False, "error": str(e)}
    print(json.dumps(result, indent=2, ensure_ascii=False))
