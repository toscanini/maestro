from distutils.core import setup
setup(name='dockermix',
    version='0.1',
    description='Tools to provision multiple Docker containers via a single command.',
    author='Kimbro Staken',
    author_email='kstaken@kstaken.com',
    url='https://github.com/kstaken/dockermix',
    packages=['dockermix'],
    scripts=['bin/dockermix']
)
