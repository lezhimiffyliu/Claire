"""
Mobile Upload Page - Streamlit page for mobile photo upload.

URL format: /upload?t=<token>

This page is optimized for mobile:
- Hidden sidebar
- Large touch targets
- Simple file upload interface
"""

import streamlit as st
from mobile_upload import (
    validate_token,
    pair_mobile_session,
    upload_image,
    close_session,
)

# Page config - must be first Streamlit command
st.set_page_config(
    page_title="Upload Solution - Claire",
    page_icon="📷",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Mobile-optimized CSS
st.markdown("""
<style>
    /* Hide sidebar completely on mobile */
    [data-testid="stSidebar"] {
        display: none;
    }
    [data-testid="stSidebarCollapsedControl"] {
        display: none;
    }

    /* Large touch targets */
    .stButton button {
        min-height: 56px !important;
        font-size: 18px !important;
        font-weight: 500;
    }

    /* Better spacing */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 600px !important;
    }

    /* File uploader styling */
    [data-testid="stFileUploader"] {
        border: 2px dashed #ccc;
        border-radius: 12px;
        padding: 20px;
    }

    /* Success/error messages */
    .stSuccess, .stError, .stWarning {
        font-size: 16px !important;
    }

    /* Problem text box */
    .problem-box {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
        font-size: 15px;
        line-height: 1.5;
        max-height: 200px;
        overflow-y: auto;
    }

    /* Image preview */
    .uploaded-preview {
        border-radius: 8px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


def render_error_page(message: str):
    """Show error page for invalid/expired tokens."""
    st.markdown("## Claire")
    st.error(message)
    st.markdown("""
    **What to do:**
    1. Go back to your computer
    2. Click "Generate New QR Code"
    3. Scan the new QR code
    """)


def render_upload_page(session):
    """Render the upload interface for a valid session."""
    st.markdown("## Upload Your Solution")

    # Show problem context
    if session.problem_display_text:
        st.markdown("**Problem:**")
        st.markdown(
            f'<div class="problem-box">{session.problem_display_text}</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    # File uploader - allow multiple files
    st.markdown("**Take photos of your work:**")
    uploaded_files = st.file_uploader(
        "Select photos",
        type=["png", "jpg", "jpeg", "heic"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="mobile_upload",
    )

    # Show previews
    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} photo(s) selected:**")
        cols = st.columns(min(len(uploaded_files), 3))
        for i, file in enumerate(uploaded_files):
            with cols[i % 3]:
                st.image(file, use_container_width=True)

        st.markdown("")

        # Upload button
        if st.button("Upload Photos", type="primary", use_container_width=True):
            progress = st.progress(0)
            success_count = 0

            for i, file in enumerate(uploaded_files):
                progress.progress((i + 1) / len(uploaded_files))

                # Read file bytes
                file_bytes = file.getvalue()
                filename = file.name

                # Detect content type
                if filename.lower().endswith(".png"):
                    content_type = "image/png"
                elif filename.lower().endswith((".jpg", ".jpeg")):
                    content_type = "image/jpeg"
                elif filename.lower().endswith(".heic"):
                    content_type = "image/heic"
                else:
                    content_type = "image/png"

                # Upload
                result, error = upload_image(
                    session_id=session.id,
                    file_bytes=file_bytes,
                    filename=filename,
                    content_type=content_type,
                )

                if result:
                    success_count += 1
                elif error:
                    st.error(f"Error: {error}")

            progress.empty()

            if success_count == len(uploaded_files):
                st.success(f"Uploaded {success_count} photo(s) successfully!")
                st.session_state.upload_complete = True
                st.rerun()
            elif success_count > 0:
                st.warning(f"Uploaded {success_count}/{len(uploaded_files)} photos. Some failed.")
            else:
                st.error("Upload failed. Please try again.")

    # Done button (after upload)
    if st.session_state.get("upload_complete"):
        st.markdown("---")
        st.success("Your photos have been uploaded!")
        st.markdown("You can close this page or upload more photos.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Upload More", use_container_width=True):
                st.session_state.upload_complete = False
                st.rerun()
        with col2:
            if st.button("Done", type="primary", use_container_width=True):
                close_session(session.id)
                st.success("Session closed. You can close this page.")
                st.stop()


def main():
    """Main entry point for upload page."""
    # Get token from query params
    token = st.query_params.get("t")

    if not token:
        render_error_page("No upload token provided. Please scan a QR code from the Claire app.")
        return

    # Validate token
    session = validate_token(token)

    if not session:
        render_error_page("This upload link has expired or is invalid. Please generate a new QR code.")
        return

    # Pair session on first access
    if session.status == "waiting":
        pair_mobile_session(session.id)
        # Re-fetch session to get updated status
        session = validate_token(token)

    # Check if session is closed
    if session.status in ["closed", "expired"]:
        render_error_page("This upload session has ended. Please generate a new QR code if needed.")
        return

    # Render upload interface
    render_upload_page(session)


# Run main
main()
