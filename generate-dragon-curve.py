#!/usr/bin/env python

# ------------------------------------------------------------------
# Copyright (C) 2013 Michael Aschauer
# ------------------------------------------------------------------
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.s
# ------------------------------------------------------------------

import stitchcode
import turtle

stmax = 30

def forward(d):
	while d != 0:
		def clamp(v):
			if (v>stmax):
				v = stmax
			return v			
		dx = clamp(d)
		turtle.forward(dx)
		emb.addStitch(stitchcode.Point(turtle.pos()[0],turtle.pos()[1]))
		d -= dx
		
def backward(d):
	turtle.right(180)
	forward(d)
	turtle.right(180)	


def dragon_build(turtle_string, n):
    """ Recursively builds a draw string. """
    """ defining f, +, -, as additional rules that don't do anything """
    rules = {'x':'x+yf', 'y':'fx-y','f':'f', '-':'-', '+':'+'}
    turtle_string = ''.join([rules[x] for x in turtle_string])
    if n > 1: return dragon_build(turtle_string, n-1)
    else: return turtle_string

def dragon_draw(size):
    """ Draws a Dragon Curve of length 'size'. """
    turtle_string = dragon_build('fx', size)
    for x in turtle_string:
        if x == 'f': forward(20)
        elif x == '+': turtle.right(90)
        elif x == '-': turtle.left(90)
        
if __name__ == "__main__":
	emb = stitchcode.Embroidery()
	turtle.speed(200)
	dragon_draw(12)
	emb.translate_to_origin()
	emb.save_as_exp("dragon-curve2.exp")
	emb.save_as_png("dragon-curve2.png",True)


