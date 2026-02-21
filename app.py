#!/usr/bin/env python3
# coding: utf-8
"""
Streamlit web app for the Baltika digit-replacement tool.

Upload an image, click 'Process', and the app will detect digits using a
pretrained EasyOCR model and overlay the custom beer bottle images in place.

Run with:
    streamlit run app.py
"""

import io
import os
import tempfile

import streamlit as st
from PIL import Image

from replace_digits import replace_digits_in_image, PICS_DIR


st.set_page_config(
    page_title='Baltika Digit Replacer',
    page_icon='🍺',
    layout='centered',
)

st.title('🍺 Baltika Digit Replacer')
st.write(
    'Upload an image containing digits. The app will detect them with a '
    'pretrained OCR model and replace each digit with a custom beer bottle image.'
)
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
    sample_paths = [os.path.join(PICS_DIR, 'sample1.png'), os.path.join(PICS_DIR, 'sample2.jpg'), os.path.join(PICS_DIR, 'sample3.png')]
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

    if st.button('Process — Replace Digits'):
        with st.spinner('Detecting and replacing digits…'):
            # Determine a safe suffix for the temp file
            ext = os.path.splitext(file_name)[1] or '.png'

            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_in:
                tmp_in.write(file_bytes)
                input_path = tmp_in.name

            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_out:
                output_path = tmp_out.name

            try:
                replace_digits_in_image(input_path, output_path, PICS_DIR)
                result_image = Image.open(output_path)

                st.subheader('Result Image')
                st.image(result_image, width=700)

                # Provide a download button
                buf = io.BytesIO()
                result_image.save(buf, format='PNG')
                st.download_button(
                    label='Download result',
                    data=buf.getvalue(),
                    file_name=f'replaced_{file_name}',
                    mime='image/png',
                )
            finally:
                os.unlink(input_path)
                if os.path.exists(output_path):
                    os.unlink(output_path)


with st.expander("See explanation"):
    st.write(
        """
        This app uses a pretrained OCR model to detect digits in your uploaded image. 
        It then replaces each detected digit with a custom beer bottle image corresponding to that digit (0-9). 
        You can upload your own image or choose from the provided sample images. 
        After processing, you can download the resulting image with the replaced digits.
        """
    )