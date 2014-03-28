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
import numpy
import math
from scipy import interpolate

stepsize_x = 2
stepsize_y = 30

def getDistance(x1, y1, x2, y2):
	dx = x1 - x2
	dy = y1 - y2
	dist = math.sqrt( dx*dx + dy*dy )
	return dist

if __name__ == "__main__":
	emb = stitchcode.Embroidery()
	emb.addStitch(stitchcode.Point(0,0))
	last_y = 0;
	x=0
	
	for j in range(0, 512):		
		if j % 1 == 0:			
			y = numpy.random.normal(0,0.5) * 127
		else:
			y = 0
		
		d = getDistance(0, last_y, stepsize_y, y)
		steps = max(1,int(round( d / stepsize_y)))

		yarr = (last_y,y)
		xarr = (0,steps+1)
		xnew = range(0,steps+1)
		
		f = interpolate.interp1d(xarr,yarr)
		ynew = f(xnew)
		print steps, y, ynew
		
		if steps == 1:
			x += stepsize_x
			emb.addStitch(stitchcode.Point(x, y))
			print (x,y)
		else:	
			for i in range(1,steps+1):
				if ((i == 1) or (i == 2 and stepsize_x < 3)):
					x += 1
						
				y = ynew[i]
				emb.addStitch(stitchcode.Point(x, y))
				last_y = y
				print (x,y)

	x = x + stepsize_x
	emb.addStitch(stitchcode.Point(x,0))
	
	emb.translate_to_origin()
	emb.save_as_exp("noise.exp")
	emb.save_as_png("noise.png",False)
