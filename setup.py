from distutils.core import setup

setup(	name="stitchcode",
		version="0.01",
		author="Michael Aschauer",
		py_modules=['stitchcode'],
		data_files=[	('bin', ['exp2png.py','exp2exp.py','exp2svg.py'])]
     )
