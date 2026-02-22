#!/usr/bin/env python3
# coding: utf-8
"""
Streamlit web app for the Baltika digit-replacement tool.

Upload an image, click 'Process', and the app will send it to the remote
backend API which detects digits with EasyOCR and returns the processed image.

Remote server connection is configured via Streamlit secrets:
    API_KEY — shared secret key for the backend API
    API_URL — base URL of the backend server, e.g. http://203.0.113.42:8000

Run with:
    streamlit run app.py
"""

import io
import os

import requests
import streamlit as st
from PIL import Image

_PICS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pics')


st.set_page_config(
    page_title='Baltika Digit Replacer',
    page_icon='🍺',
    layout='centered',
    initial_sidebar_state='expanded',
)

st.title('🍺 Baltika Digit Replacer')
st.write(
    'Upload an image containing digits. The app will detect them with a '
    'pretrained OCR model and replace each digit with a custom beer bottle image.'
)
with st.expander("How it works"):
    st.write(
        """
        This app uses a pretrained OCR model to detect digits in your uploaded image. 
        It then replaces each detected digit with a custom beer bottle image corresponding to that digit (0-9). 
        You can upload your own image or choose from the provided sample images. 
        After processing, you can download the resulting image with the replaced digits.
        """
    )
    # Show the example image instead of the digit montage
    try:
        example_path = os.path.join(_PICS_DIR, 'example.jpg')
        if os.path.exists(example_path):
            with open(example_path, 'rb') as f:
                img_bytes = f.read()
            st.image(img_bytes, width=700)
    except Exception as e:
        st.write(f'Could not load example image: {e}')

uploaded_file = st.file_uploader(
    'Choose an image', type=['png', 'jpg', 'jpeg', 'bmp', 'webp']
)

# Session state to hold a chosen sample image (bytes + name)
if 'uploaded_sample_bytes' not in st.session_state:
    st.session_state['uploaded_sample_bytes'] = None
    st.session_state['uploaded_sample_name'] = None

with st.expander("Example inputs"):    
    # Display example images with buttons to load them
    col1, col2, col3 = st.columns(3)
    sample_paths = [os.path.join(_PICS_DIR, 'sample1.png'), os.path.join(_PICS_DIR, 'sample2.jpg'), os.path.join(_PICS_DIR, 'sample3.png')]
    with col1:
        st.image(Image.open(sample_paths[0]), caption='Sample 1', width=200)
        if st.button('Use Sample 1'):
            with open(sample_paths[0], 'rb') as f:
                st.session_state['uploaded_sample_bytes'] = f.read()
                st.session_state['uploaded_sample_name'] = 'sample1.png'
    with col2:
        st.image(Image.open(sample_paths[1]), caption='Sample 2', width=220)
        if st.button('Use Sample 2'):
            with open(sample_paths[1], 'rb') as f:
                st.session_state['uploaded_sample_bytes'] = f.read()
                st.session_state['uploaded_sample_name'] = 'sample2.jpg'
    with col3:
        st.image(Image.open(sample_paths[2]), caption='Sample 3', width=240)
        if st.button('Use Sample 3'):
            with open(sample_paths[2], 'rb') as f:
                st.session_state['uploaded_sample_bytes'] = f.read()
                st.session_state['uploaded_sample_name'] = 'sample3.png'


# ---------------------------------------------------------------------------
# Load API configuration from Streamlit secrets
# ---------------------------------------------------------------------------
_api_ready = True

try:
    _API_KEY = st.secrets["API_KEY"]
    _API_URL = st.secrets["API_URL"].rstrip("/")
except KeyError as _e:
    st.warning(
        f"⚠️ Remote server is not configured: missing secret **{_e.args[0]}**. "
        "Create `.streamlit/secrets.toml` with `API_KEY` and `API_URL` "
        "(see `.streamlit/secrets.toml.example`)."
    )
    _api_ready = False
except Exception as _e:
    st.warning(f"⚠️ Could not read Streamlit secrets: {_e}")
    _api_ready = False


def _call_api(image_bytes: bytes, filename: str) -> bytes:
    """Send *image_bytes* to the remote API and return the processed PNG bytes."""
    url = f"{_API_URL}/process"
    mime = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
    response = requests.post(
        url,
        files={"file": (filename, image_bytes, mime)},
        headers={"X-API-Key": _API_KEY},
        timeout=120,
    )
    response.raise_for_status()
    return response.content


file_bytes = None
file_name = None
if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    file_name = uploaded_file.name
elif st.session_state.get('uploaded_sample_bytes'):
    file_bytes = st.session_state['uploaded_sample_bytes']
    file_name = st.session_state['uploaded_sample_name']

if file_bytes is not None:
    original_image = Image.open(io.BytesIO(file_bytes))
    st.subheader('Original Image')
    st.image(original_image, width=700)

    if st.button('Process — Replace Digits', disabled=not _api_ready):
        with st.spinner('Sending image to the remote server…'):
            try:
                result_bytes = _call_api(file_bytes, file_name or 'image.png')
                result_image = Image.open(io.BytesIO(result_bytes))

                st.subheader('Result Image')
                st.image(result_image, width=700)

                # Provide a download button
                st.download_button(
                    label='Download result',
                    data=result_bytes,
                    file_name=f'replaced_{file_name}',
                    mime='image/png',
                )
            except requests.exceptions.ConnectionError:
                st.error(
                    "❌ Cannot reach the remote server. "
                    "Check that the server is running and that `API_URL` in "
                    "`.streamlit/secrets.toml` is correct."
                )
            except requests.exceptions.Timeout:
                st.error(
                    "❌ The request to the remote server timed out. "
                    "The server may be overloaded — please try again later."
                )
            except requests.exceptions.HTTPError as exc:
                if exc.response is not None and exc.response.status_code == 401:
                    st.error(
                        "❌ Authentication failed. "
                        "Check that `API_KEY` in `.streamlit/secrets.toml` matches "
                        "the key configured on the server."
                    )
                else:
                    st.error(f"❌ Server returned an error: {exc}")
