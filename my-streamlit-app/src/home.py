import streamlit as st

class StreamlitApp:
    def __init__(self):
        self.user_credentials = {"admin": "123"}  # Change as needed
        self.setup_page_config()
        self.initialize_session_state()

    def setup_page_config(self):
        st.set_page_config(
            page_title="Login",
            page_icon="🔐",
            layout="centered",
            menu_items={}  # ✅ This removes the default Streamlit navigation
        )

    def initialize_session_state(self):
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False

    def login_page(self):
        st.title("🔐 Login Page")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username in self.user_credentials and self.user_credentials[username] == password:
                st.session_state.authenticated = True
                st.success("Login successful! Redirecting...")
                st.rerun()  # ✅ Redirects to the app
            else:
                st.error("Invalid username or password")

    def main_app(self):
        with st.sidebar:
            st.title("Navigation")
            page = st.radio("Go to", ["Home", "Page 1", "Page 2"])

            if st.button("Logout"):
                st.session_state.authenticated = False
                st.rerun()  # ✅ Redirects back to login

        if page == "Home":
            self.home_page()
        elif page == "Page 1":
            self.page1()
        elif page == "Page 2":
            self.page2()

    def home_page(self):
        st.title("🏠 Welcome to My Streamlit App")
        st.write("You are logged in!")

    def page1(self):
        import page.page1 as Page1
        Page1.main()

    def page2(self):
        import page.page2 as Page2
        Page2.run()

    def run(self):
        if not st.session_state.authenticated:
            self.login_page()
        else:
            self.main_app()

if __name__ == "__main__":
    app = StreamlitApp()
    app.run()
