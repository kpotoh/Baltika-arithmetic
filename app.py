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

import numpy as np
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

if uploaded_file is not None:
    original_image = Image.open(uploaded_file)
    st.subheader('Original Image')
    st.image(original_image, use_container_width=True)

    if st.button('Process — Replace Digits'):
        with st.spinner('Detecting and replacing digits…'):
            # Determine a safe suffix for the temp file
            ext = os.path.splitext(uploaded_file.name)[1] or '.png'

            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_in:
                tmp_in.write(uploaded_file.getvalue())
                input_path = tmp_in.name

            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_out:
                output_path = tmp_out.name

            try:
                replace_digits_in_image(input_path, output_path, PICS_DIR)
                result_image = Image.open(output_path)

                st.subheader('Result Image')
                st.image(result_image, use_container_width=True)

                # Provide a download button
                buf = io.BytesIO()
                result_image.save(buf, format='PNG')
                st.download_button(
                    label='Download result',
                    data=buf.getvalue(),
                    file_name=f'replaced_{uploaded_file.name}',
                    mime='image/png',
                )
            finally:
                os.unlink(input_path)
                if os.path.exists(output_path):
                    os.unlink(output_path)
