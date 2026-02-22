#!/usr/bin/env python3
# coding: utf-8

"""
Legacy Baltika Digit Replacer page for Streamlit.
This reproduces the functionality of `baltika.py`: build an image from a string
of digits and operators and optionally compute the arithmetic result.
"""

import io
import os
import streamlit as st
from PIL import Image

PICS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pics')

st.set_page_config(page_title='Legacy Baltika', page_icon='🍺', layout='centered')
st.title('Legacy Baltika Digit Replacer')

st.write('Enter an expression composed of digits and operators (+ - * /).')
expr_input = st.text_input('Expression', value='123+456')
cols = st.columns(2)
with cols[0]:
    with_calc = st.checkbox('Calculate result and append "=answer"', value=False)
with cols[1]:
    width = st.slider('Digit image width (px)', 80, 400, 150)

def _load_assets(pics_dir, width):
    nums = [Image.open(os.path.join(pics_dir, f'{i}.png')).convert('RGBA') for i in range(10)]
    nums_resized = [pic.resize((width, max(1, int(pic.size[1] / pic.size[0] * width)))) for pic in nums]

    sign_files = {
        '.': 'dot.png',
        '+': 'plus.png',
        '-': 'minus.png',
        '/': 'div.png',
        '*': 'mult.png',
        '=': 'ravno.png',
    }
    signs = {}
    for k, fname in sign_files.items():
        path = os.path.join(pics_dir, fname)
        if os.path.exists(path):
            pic = Image.open(path).convert('RGBA')
            signs[k] = pic.resize((width, max(1, int(pic.size[1] / pic.size[0] * width))))
    return nums_resized, signs


def _to_code(s: str):
    s = s.split('=')[0]
    code = []
    expr_tokens = []
    tmp = ''
    for c in s:
        if c not in '0123456789.+-/*':
            continue
        if c in '0123456789.':
            tmp += c
        if c in '+-/*':
            expr_tokens.append(tmp)
            expr_tokens.append(c)
            tmp = ''
        code.append(c)
    expr_tokens.append(tmp)
    return code, expr_tokens


def _binar_oper(a, b, op):
    if op == '*':
        return a * b
    if op == '/':
        return a / b
    if op == '+':
        return a + b
    if op == '-':
        return a - b
    raise ValueError('Unknown operator')


def _result_of_expr(tokens):
    # tokens is list like ['12', '+', '3', '*', '4']
    # convert numbers to float and keep operators
    expr = []
    for t in tokens:
        if t in '+-/*':
            expr.append(t)
        else:
            try:
                expr.append(float(t) if t != '' else 0.0)
            except Exception:
                expr.append(0.0)

    for op in '*/+-':
        while op in expr:
            i = expr.index(op)
            a = float(expr[i-1])
            b = float(expr[i+1])
            val = _binar_oper(a, b, op)
            # replace a,op,b with val
            expr[i-1:i+2] = [val]
    if len(expr) == 1:
        v = expr[0]
        if abs(v - int(v)) < 1e-9:
            return int(v)
        return round(v, 2)
    return None


def _make_image(code, nums, signs, n_width=150, height=None):
    if not nums:
        raise RuntimeError('Digit assets not found')
    widths = [im.size[0] for im in nums]
    heights = [im.size[1] for im in nums]
    max_h = max(heights)
    if height is None:
        height = max_h
    total_w = len(code) * n_width
    out = Image.new('RGBA', (total_w, height), (255, 255, 255, 255))
    x = 0
    for c in code:
        if c in '0123456789':
            im = nums[int(c)]
            out.paste(im, (x, height - im.size[1]), im)
            x += im.size[0]
        else:
            im = signs.get(c)
            if im is None:
                # skip unknown char
                continue
            out.paste(im, (x, height - im.size[1]), im)
            x += n_width
    return out.convert('RGB')


if st.button('Generate Image'):
    try:
        nums, signs = _load_assets(PICS_DIR, width)
        code, tokens = _to_code(expr_input)
        if with_calc:
            res = _result_of_expr(tokens)
            if res is None:
                st.error('Could not calculate expression.')
            else:
                code.append('=')
                code += list(str(res))
        img = _make_image(code, nums, signs, n_width=width)
        st.image(img, width=700)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        st.download_button('Download', data=buf.getvalue(), file_name='legacy.png', mime='image/png')
    except Exception as e:
        st.error(f'Error: {e}')
