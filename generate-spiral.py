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

def f(dist, angle, incr, segs):
	for i in range(segs):
		forward(dist * (600))
		turtle.right(angle)
		dist += incr

if __name__ == "__main__":
	emb = stitchcode.Embroidery()
	turtle.speed(200)
	f(.01, 89.5, .01, 150)
	emb.translate_to_origin()
	emb.write_exp("spiral.exp")
	emb.save_as_png("spiral.png",True)
