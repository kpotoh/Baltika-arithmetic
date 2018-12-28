#!/usr/bin/env python3.6
# coding: utf-8

import sys
from PIL import Image
from PIL import ImageFilter
import numpy as np
import matplotlib.pyplot as plt

# defaulf values
EXP, OUT_FILE, WC = '777', None, False

# read options
for x in ['-s', '--string']:
	if x in sys.argv:
		EXP = sys.argv[sys.argv.index(x) + 1]

for x in ['--out_file', '-o']:
	if x in sys.argv:
		OUT_FILE = sys.argv[sys.argv.index(x) + 1]

if '--with_calc' in sys.argv or '-w' in sys.argv:
	WC = True


# load nums resize nums with WIDTH and appropriate height
WIDTH = 300
ims = [Image.open('./pics/{}.png'.format(i)) for i in range(10)]
n_ims = [pic.resize((WIDTH, int(pic.size[1] / pic.size[0] * WIDTH))) for pic in ims]


# load signs and get dict
pre_signs = [Image.open('./pics/{}.png'.format(i)) for i in ['dot','plus','minus','div','mult','ravno']]
signs = [pic.resize((WIDTH, int(pic.size[1] / pic.size[0] * WIDTH))) for pic in pre_signs]
sign_dict = {x:y for x,y in zip(list('.+-/*='), signs)}


# items for generating of image form
widths, heights = zip(*(i.size for i in n_ims))


total_width = sum(widths)
max_height = max(heights)

# create list of single characters and list of nums with operations for calculation
def to_code(mystr):
    mystr = mystr.split('=')[0]
    result = []
    for_ex = []
    tmp_n = ''
    for c in list(mystr):
        if c == '' or c not in '1234567890.+/-*':
            continue
        if c in '1234567890.':
            tmp_n += c
        if c in '+-/*':
            for_ex.append(tmp_n)
            for_ex.append(c)
            tmp_n = ''
        result.append(c)
    for_ex.append(tmp_n)
    return result, for_ex


# create final image using sigle character code
def make_image(code, nums, signs, height=max_height, n_width=WIDTH):
    width = len(''.join(code)) * n_width
    new_im = Image.new('RGB', (width, height), (255,255,255))
    x_offset = 0
    for c in code:
        if c in '1234567890':
            im = nums[int(c)]
            new_im.paste(im, (x_offset, max_height-im.size[1]))
            x_offset += im.size[0]
        else:
            im = signs[c]
            new_im.paste(im, (x_offset, max_height-im.size[1]))
            x_offset += n_width
    return new_im


# apply operator to 2 nums
def binar_oper(n1, n2, oper):
    if oper == '*':
        return n1 * n2
    if oper == '/':
        return n1 / n2
    if oper == '+':
        return n1 + n2
    if oper == '-':
        return n1 - n2


# calculation func (with arithmetic rules)
def result_of_expr(expr):
    for S in '*/+-':
        for j in range(expr.count(S)):
            fid = expr.index(S)
            new_c = binar_oper(float(expr[fid-1]), float(expr[fid+1]), S)
            expr.pop(fid-1); expr.pop(fid-1); expr.pop(fid-1)
            expr.insert(fid-1, new_c)
    
    # rounding
    if len(expr) == 1:
        if expr[0] == int(expr[0]):
            return int(expr[0])
        return round(expr[0], 2)
    else:
        return 8888 # error code


# pipeline func
def save_and_show(inp, name, w_calc=True):
    code, expr = to_code(inp)
    if w_calc == True:
        ans_expr = result_of_expr(expr) # calculation result
        code.append('=')
        code += list(str(ans_expr))
    new_pic = make_image(code, nums=n_ims, signs=sign_dict)
    if name:
        new_pic.save(name, 'png')
    else:
	    new_pic.show()

save_and_show(EXP, OUT_FILE, WC)
