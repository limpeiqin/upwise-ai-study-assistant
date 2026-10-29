
import streamlit as st
from pathlib import Path
from supabase_client import supabase
import base64


def show_auth_page():
    # Find and load the logo
    project_dir = Path(__file__).resolve().parent
    logo_path = project_dir / "assets" / "Upwise_Logo.png"

    # Place logo close to the welcome heading
    if logo_path.is_file():
        with open(logo_path, "rb") as image_file:
            logo_base64 = base64.b64encode(
                image_file.read()
            ).decode("utf-8")

        st.markdown(
            f"""
            <div style="
                display: flex;
                align-items: center;
                gap: 0px;
                margin-bottom: 8px;
                flex-wrap: nowrap;
            ">
                <h1 style="
                    margin: 0;
                    padding: 0;
                    font-size: 2.6rem;
                    font-weight: 700;
                    line-height: 1.2;
                    white-space: nowrap;
                ">Welcome to Upwise</h1>
                <img
                    src="data:image/png;base64,{logo_base64}"
                    style="
                        width: 135px;
                        height: 100px;
                        object-fit: contain;
                        flex-shrink: 0;
                        margin-left: -35px;
                    "
                />
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.title("Welcome to Upwise")
        st.error(f"Logo file not found: {logo_path}")

    st.write("Your Personal AI Learning Companion")

    # Sign In and Sign Up tabs
    tab_login, tab_signup = st.tabs(["Sign In", "Sign Up"])

    # Sign In
    with tab_login:
        with st.form("login_form"):
            email = st.text_input(
                "Email",
                key="login_email"
            )

            password = st.text_input(
                "Password",
                type="password",
                key="login_password"
            )

            login_clicked = st.form_submit_button("Sign In")

        if login_clicked:
            try:
                result = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })

                st.session_state["user"] = result.user
                st.session_state["session"] = result.session

                st.rerun()

            except Exception as e:
                st.error(f"Login failed: {e}")

    # Sign Up
    with tab_signup:
        with st.form("signup_form"):
            email = st.text_input(
                "Email",
                key="signup_email"
            )

            password = st.text_input(
                "Password",
                type="password",
                key="signup_password"
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                key="confirm_password"
            )

            signup_clicked = st.form_submit_button("Create Account")

        if signup_clicked:
            if password != confirm_password:
                st.error("Passwords do not match.")

            elif len(password) < 8:
                st.error(
                    "Password must contain at least 8 characters."
                )

            else:
                try:
                    result = supabase.auth.sign_up({
                        "email": email,
                        "password": password
                    })

                    if result.session is not None:
                        st.session_state["user"] = result.user
                        st.session_state["session"] = result.session
                        st.rerun()

                    else:
                        st.success(
                            "Account created! Please check your email "
                            "to confirm your account before signing in."
                        )

                except Exception as e:
                    st.error(f"Sign up failed: {e}")
