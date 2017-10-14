from distutils.core import setup


setup(	name="stitchcode",
		version="0.2",
		author="Michael Aschauer",
		author_email="m@ash.to",
		py_modules=['stitchcode'],
		license='LICENSE.txt',
		description='Embroidery tools for python',
		long_description=open('README.txt').read(),
		url='https://github.com/backface/stitchcode',
		#data_files=[
		#('bin', 
		#	['exp2png.py',
		#	'exp2exp.py',
		#	'exp2svg.py',
		#	'stitchconv.py']
		#)]
		scripts=['stitchconv.py'],
     )
