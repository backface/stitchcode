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


maxstep = 30
maxx = 800
maxy = 600

if __name__ == "__main__":
	emb = stitchcode.Embroidery()
	(x,y) = (0,0)
	
	for i in range(0,4000):	
		
		sx = numpy.random.normal(0,1) * maxstep
		sy = numpy.random.normal(0,1) * maxstep

		
		if (x + sx < 0):
			sx *= -1
		if (x + sx > maxx):
			sx *= -1
		x += sx
			
		if (y + sy < 0):
			sy *= -1
		if (y + sy > maxy):
			sy *= -1

		y += sy	

		print x,y, "/", sx,sy			
		emb.addStitch(stitchcode.Point(x,y))
	
	emb.scale(1)
	emb.translate_to_origin()
	emb.save_as_exp("random-walk.exp")
	emb.save_as_png("random-walk.png",False)
