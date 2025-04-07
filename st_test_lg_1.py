
import streamlit as st
import requests
import os
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

# App title and configuration
st.set_page_config(page_title="Streamlit Google Auth Demo", layout="centered")

# Get credentials from environment variables
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "https://your-app-name.streamlit.app")

# OAuth2 scope for basic profile information
SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email',
          'https://www.googleapis.com/auth/userinfo.profile']

# Initialize session state variables
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False


def create_flow():
    """Create OAuth 2.0 flow instance to manage the OAuth 2.0 Authorization Grant Flow steps."""
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI]
            }
        },
        scopes=SCOPES
    )
    flow.redirect_uri = REDIRECT_URI
    return flow


def get_authorization_url():
    """Get the authorization URL to redirect the user to."""
    flow = create_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    return authorization_url


def exchange_code_for_token(code):
    """Exchange authorization code for token."""
    flow = create_flow()
    flow.fetch_token(code=code)
    credentials = flow.credentials
    return credentials


def get_user_info(credentials):
    """Get user info from Google API."""
    response = requests.get(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers={'Authorization': f'Bearer {credentials.token}'}
    )
    if response.status_code == 200:
        return response.json()
    return None


def sign_out():
    """Sign out the user by resetting session state."""
    st.session_state.user_info = None
    st.session_state.is_authenticated = False
    st.session_state.credentials = None


def display_user_info():
    """Display user information."""
    if st.session_state.user_info:
        st.write(f"### Welcome, {st.session_state.user_info.get('name', 'User')}!")

        col1, col2 = st.columns([1, 3])

        with col1:
            picture_url = st.session_state.user_info.get('picture')
            if picture_url:
                st.image(picture_url, width=100)

        with col2:
            st.write(f"**Email:** {st.session_state.user_info.get('email', 'Not available')}")
            st.write(f"**Google ID:** {st.session_state.user_info.get('id', 'Not available')}")

        st.button("Sign Out", on_click=sign_out)
    else:
        st.error("User information is not available.")


def main():
    st.title("Streamlit Google Authentication")

    # Check if credentials are properly set
    if not CLIENT_ID or not CLIENT_SECRET:
        st.error(
            "Google OAuth credentials are not set. Please set the GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.")
        st.info(
            "For local development, you can use:\n```\nexport GOOGLE_CLIENT_ID=your_client_id\nexport GOOGLE_CLIENT_SECRET=your_client_secret\nexport REDIRECT_URI=your_redirect_uri\n```")
        return

    # Check for query parameters in URL
    query_params = st.experimental_get_query_params()
    code = query_params.get("code", [None])[0]

    # If user is already authenticated, show their info
    if st.session_state.is_authenticated and st.session_state.user_info:
        display_user_info()

        # Here you can add your application content for authenticated users
        st.write("## Your Application Content")
        st.write("This is the protected area of your application.")

    # If we have a code parameter, exchange it for token and get user info
    elif code:
        with st.spinner("Completing authentication..."):
            try:
                credentials = exchange_code_for_token(code)
                user_info = get_user_info(credentials)

                if user_info:
                    st.session_state.user_info = user_info
                    st.session_state.is_authenticated = True
                    st.session_state.credentials = {
                        'token': credentials.token,
                        'refresh_token': credentials.refresh_token,
                        'token_uri': credentials.token_uri,
                        'client_id': credentials.client_id,
                        'client_secret': credentials.client_secret,
                        'scopes': credentials.scopes
                    }

                    # Clear the URL parameters
                    st.experimental_set_query_params()
                    st.experimental_rerun()
                else:
                    st.error("Failed to get user information.")
            except Exception as e:
                st.error(f"Authentication error: {str(e)}")

    # If not authenticated, show login button
    else:
        st.write("### Please sign in to continue")
        st.markdown("""
        This application requires Google authentication.
        Click the button below to sign in with your Google account.
        """)

        auth_url = get_authorization_url()
        st.markdown(f'''
        <a href="{auth_url}" target="_self">
            <button style="
                background-color: #4285F4;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                cursor: pointer;
                display: flex;
                align-items: center;
                ">
                <svg style="margin-right: 10px;" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="24px" height="24px">
                    <path fill="#FFC107" d="M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12c0-6.627,5.373-12,12-12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C12.955,4,4,12.955,4,24c0,11.045,8.955,20,20,20c11.045,0,20-8.955,20-20C44,22.659,43.862,21.35,43.611,20.083z"/>
                    <path fill="#FF3D00" d="M6.306,14.691l6.571,4.819C14.655,15.108,18.961,12,24,12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C16.318,4,9.656,8.337,6.306,14.691z"/>
                    <path fill="#4CAF50" d="M24,44c5.166,0,9.86-1.977,13.409-5.192l-6.19-5.238C29.211,35.091,26.715,36,24,36c-5.202,0-9.619-3.317-11.283-7.946l-6.522,5.025C9.505,39.556,16.227,44,24,44z"/>
                    <path fill="#1976D2" d="M43.611,20.083H42V20H24v8h11.303c-0.792,2.237-2.231,4.166-4.087,5.571c0.001-0.001,0.002-0.001,0.003-0.002l6.19,5.238C36.971,39.205,44,34,44,24C44,22.659,43.862,21.35,43.611,20.083z"/>
                </svg>
                Sign in with Google
            </button>
        </a>
        ''', unsafe_allow_html=True)

        st.write("You will be redirected to Google for authentication.")


if __name__ == "__main__":
    main()
