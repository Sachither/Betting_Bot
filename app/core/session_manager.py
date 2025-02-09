from playwright.sync_api import sync_playwright

class SessionManager:
    """
    Manages asynchronous Playwright browser sessions for users.
    """
    def __init__(self):
        self.sessions = {}  # Dictionary to store user sessions

    def start_session(self, user_id):
        """
        Start a new browser session for a user.
        """
        if user_id in self.sessions:
            return self.sessions[user_id]  # Return the existing session

        # Create a new Playwright instance and browser session
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        # Store the session details
        self.sessions[user_id] = {
            "playwright": playwright,
            "browser": browser,
            "page": page,
        }
        return self.sessions[user_id]

    def get_session(self, user_id):
        """
        Retrieve the session for a user.
        """
        return self.sessions.get(user_id)

    def close_session(self, user_id):
        """
        Close the browser session for a user.
        """
        if user_id in self.sessions:
            session = self.sessions.pop(user_id)
            session["browser"].close()
            session["playwright"].stop()
