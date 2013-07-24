from distutils.core import setup
setup(name='maestro',
    version='0.1',
    description='Orchestration tools for multi-container docker environments',
    author='Kimbro Staken',
    author_email='kstaken@kstaken.com',
    url='https://github.com/kstaken/dockermix',
    packages=['maestro'],
    scripts=['bin/maestro']
)
