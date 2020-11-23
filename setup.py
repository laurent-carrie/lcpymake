from setuptools import setup, find_packages

setup(name='lcpymake', packages=find_packages(),
      entry_points={
          'console_scripts':
              ['lcpymake = lcpymake.cli:main'
               ]}

      )
