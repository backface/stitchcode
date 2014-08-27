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

stmax = 25

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

def circle(d, steps):
	for i in range(steps):
		forward(d)
		turtle.right(360 / steps)

if __name__ == "__main__":
	emb = stitchcode.Embroidery()
	turtle.speed(2000)
	steps = 100
	s = 50
	emb.addStitch(stitchcode.Point(0,0))
	for i in range(30):
		circle(s,40)
		turtle.right(12)
		#s += 1
	emb.translate_to_origin()
	emb.save_as_exp("circles.exp")
	emb.save_as_png("circles.png",True)
