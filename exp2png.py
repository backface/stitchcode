#!/usr/bin/env python
#######################################
#
# renders an EXP embroidery file as a PNG image
#
# author:(c) Michael Aschauer <m AT ash.to>
# www: http:/m.ash.to
# licenced under: GPL v3
# see: http://www.gnu.org/licenses/gpl.html
#
#######################################

from PIL import Image
import stitchcode
import getopt
import sys

def usage():
	print """
usage: exp2png.py [options] -i EXP-FILE -o PNG-FILE

renders an EXP embroidery file as a PNG image

options:
    -h, --help              print usage
    -i, --input=FILE        input EXP file
    -o, --output=FILE       output PNG file
    -z, --zoom=FACTOR       zoom in/out
"""

infile = "";
outfile = "";
zoom = 1

def process_args():
	global infile, outfile, zoom
	
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hi:o:z:",
			["help", "input=","output=","zoom="])
	except getopt.GetoptError, err:
		# print help information and exit:
		print str(err) # will print something like "option -a not recognized"
		usage()
		sys.exit(2)

	for o, a in opts:
		if o in ("-h", "--help"):
			usage()
			sys.exit()
		elif o in ("-o", "--output"):
			outfile = a
		elif o in ("-i", "--input"):
			infile = a
		elif o in ("-z", "--zoom"):
			zoom = float(a)
		else:
			assert False, "unhandled option"

	if len(infile) == 0:
		print "required."
		usage()
		sys.exit(2)
		

if __name__ == '__main__':
	process_args()
	
	if not outfile:
		outfile = "%s.png" % infile[:-4] 

	emb = stitchcode.Embroidery()
	emb.import_melco(infile)
	if zoom != 1:
		emb.scale(zoom)
	emb.translate_to_origin()
	emb.save_as_png(outfile)

		
