#from playwright.sync_api import sync_playwright

def validate_sportybet_credentials(user_id, phone_number, password, session_manager, refresh_only=False):
    """
    Validate user credentials or refresh the balance using Playwright.
    """
    print(f"Debug: Running {'refresh' if refresh_only else 'login'} process for user_id={user_id}")

    # Get or create the user's session
    session = session_manager.start_session(user_id)
    page = session["page"]

    if not refresh_only:
        # Login flow
        print("Debug: Navigating to login page...")
        page.goto("https://www.sportybet.com/ng/login", timeout=90000)
        page.fill("input[name='phone']", phone_number)
        page.fill("input[type='password']", password)
        page.click("button.af-button")
        try:
            page.wait_for_selector(".m-balance", timeout=30000)
            balance = page.locator(".m-balance").inner_text()
            return {"success": True, "balance": balance}
        except Exception as e:
            print(f"Debug: Failed to find balance. Error: {e}")
            return {"success": False, "message": "Failed to login or fetch balance."}
    else:
        # Refresh balance flow
        print("Debug: Refreshing balance...")
        try:
            page.click("#j_refreshBalance")  # Click the refresh button
            page.wait_for_timeout(6000)  # Wait for balance to update
            balance = page.locator(".m-balance").inner_text()
            return {"success": True, "balance": balance}
        except Exception as e:
            print(f"Debug: Failed to refresh balance. Error: {e}")
            return {"success": False, "message": "Failed to refresh balance."}
