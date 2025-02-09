from playwright.sync_api import sync_playwright

def debug_playwright():
    try:
        with sync_playwright() as p:
            print("Available browsers:")
            print(f"Chromium executable path: {p.chromium.executable_path}")
            print(f"Firefox executable path: {p.firefox.executable_path}")
            print(f"WebKit executable path: {p.webkit.executable_path}")
    except Exception as e:
        print(f"Playwright failed with error: {e}")

debug_playwright()
