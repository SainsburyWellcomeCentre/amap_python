from setuptools import setup, find_packages

requirements = [
    'psutil',
    'numpy>=1.12',
    'scipy',
    'scikit-image',
    'tifffile',
    'nibabel',
    'tqdm',
    'configobj'
]

optional_requirements = [
    'pytest'
]

setup(
    name='python_amap',
    version='1.0.0',
    packages=find_packages(exclude=['doc', 'tests*']),
    install_requires=requirements,
    url='',
    license='',
    author='Christian Niedworok and Charly Rousseau',
    author_email='',
    description='aMAP is a tool for optimized automated mouse atlas propagation '
                'based on clinical registration software (NiftyReg) for anatomical segmentation '
                'of high-resolution 3D fluorescence images of the adult mouse brain.',
    classifiers=[
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Science/Research'
    ]
)
