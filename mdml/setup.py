from setuptools import setup

setup(
    name='mdml',
    packages=['mdml'], 
    version='0.1.0',
    author='Benjamin J. Shields',
    author_email='shields.benjamin.j@gmail.com',
    keywords=['MD', 'Machine Learning'],
    description='Simulation Fingerprint Machine Learning Models.',
    install_requires=[
        'pandas',
        'numpy',
        'scikit-learn',
        'matplotlib',
        'dill',
        'pyarrow',
        'tqdm'
    ],
    classifiers=[
        'Development Status  3 - Alpha',
        'Intended Audience  ScienceResearch', 
        'Topic  ScientificEngineering  Chemistry',
        'Programming Language  Python  3',
    ],
    scripts=[
        'bin/mdml_train',
        'bin/mdml_predict',
        'bin/polynomial_features'
    ]
)
