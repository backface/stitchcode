#!/usr/bin/env python

#------------------------------
# EmbScribbler
#------------------------------
# Copyright (C) 2013 Michael Aschauer
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import math
import stitchcode
import pyglet
from pyglet.gl import *

width = 800
height = 400
pixels_per_millimeter = 6
min_distance_pixels = 10	

class EmbScribbler(pyglet.window.Window):
	def __init__(self):
		super(EmbScribbler, self).__init__( 
			width=width, 
			height=height, 
			resizable=False,
			caption="EmbScribbler")
		self.file_name = "scribble.exp"
		self.clear_data()
		self.jump = False
		glClearColor(1, 1, 1, 1)
	
	def clear_data(self):
		self.emb = stitchcode.Embroidery()
		self.points = []
		self.last_point = 0	
		
	def save(self):
		if len(self.points) > 0:
			self.emb.translate_to_origin()
			self.emb.scale(10.0/pixels_per_millimeter)
			#self.emb.flatten()	
			#self.emb.to_triple_stitches()
			#self.emb.add_endstitches_to_jumps()
			#self.emb.add_endstitches()
			self.emb.save_as_exp(self.file_name)
			print("saved as: %s" % self.file_name)

	def isDistanceOK(self,x,y):
		if self.last_point == 0:
			return True
		else:
			dist = math.sqrt( 
					math.pow(self.last_point[0] - x,2) 
					+ math.pow(self.last_point[1] - y,2) )
			if dist >= min_distance_pixels:	
				return True
			else:			
				#print("point too near! (distance: %f pixels" % dist)	
				return False
		
	def addPoint(self, x,y):
		if self.isDistanceOK(x,y):
			self.points.append((x,y,self.jump))
			self.last_point = (x,y,self.jump)	
			self.emb.addStitch(stitchcode.Point(x,y,self.jump))	
			self.jump = False	    
			
	def on_mouse_press(self, x, y, button, modifiers):
		if button == pyglet.window.mouse.LEFT:
			self.addPoint(x,y)

	def on_mouse_drag(self,x, y, dx, dy, button, modifiers):
		if button == pyglet.window.mouse.LEFT:
			self.addPoint(x,y)

	def on_key_press(self, symbol, modifiers):
		if symbol == pyglet.window.key.C:
			self.clear_data()
		elif symbol == pyglet.window.key.S:
			self.save()
		elif symbol == pyglet.window.key.J:
			self.jump = True			
		elif symbol == pyglet.window.key.ESCAPE:
			exit() 	
						
	def on_draw(self):
		self.clear()
		glShadeModel(GL_FLAT)
		glColor3f(0,0,0)			
		glBegin(GL_LINE_STRIP)
		for p in self.points:
			if p[2]:
				glColor3f(1,0,0)
				glVertex2i(p[0], p[1])
				glColor3f(0,0,0)
			else:
				glVertex2i(p[0], p[1])
			
		glEnd()
		
if __name__ == "__main__":
	window = EmbScribbler()
	pyglet.app.run()
