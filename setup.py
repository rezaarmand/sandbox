
import numpy
from setuptools import setup
from setuptools.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [Extension("sandbox.predictors.TreeCriterion", ["sandbox/predictors/TreeCriterion.pyx"]),
    Extension("sandbox.util.SparseUtilsCython", ["sandbox/util/SparseUtilsCython.pyx"], include_dirs=[numpy.get_include()], extra_compile_args=["-O3", ]),
    Extension("sandbox.recommendation.SGDNorm2RegCython", ["sandbox/recommendation/SGDNorm2RegCython.pyx"], include_dirs=[numpy.get_include()]), 
    Extension("sandbox.util.CythonUtils", ["sandbox/util/CythonUtils.pyx"], include_dirs=[numpy.get_include()], extra_compile_args=["-O3", ]), 
    Extension("sandbox.recommendation.MaxAUCTanh", ["sandbox/recommendation/MaxAUCTanh.pyx", "sandbox/util/CythonUtils.pyx"], include_dirs=[numpy.get_include()], extra_compile_args=["-O3", ]),
    Extension("sandbox.recommendation.MaxAUCHinge", ["sandbox/recommendation/MaxAUCHinge.pyx", "sandbox/util/CythonUtils.pyx"], include_dirs=[numpy.get_include()], extra_compile_args=["-O3", ]),
    Extension("sandbox.recommendation.MaxAUCSquare", ["sandbox/recommendation/MaxAUCSquare.pyx", "sandbox/util/CythonUtils.pyx"], include_dirs=[numpy.get_include()], extra_compile_args=["-O3", ]),
    Extension("sandbox.recommendation.MaxAUCLogistic", ["sandbox/recommendation/MaxAUCLogistic.pyx", "sandbox/util/CythonUtils.pyx"], include_dirs=[numpy.get_include()], extra_compile_args=["-O3", ]), 
    Extension("sandbox.recommendation.MaxAUCSigmoid", ["sandbox/recommendation/MaxAUCSigmoid.pyx", "sandbox/util/CythonUtils.pyx"], include_dirs=[numpy.get_include()], extra_compile_args=["-O3", ]),    
    Extension("sandbox.util.MCEvaluatorCython", ["sandbox/util/MCEvaluatorCython.pyx", "sandbox/util/CythonUtils.pyx"], include_dirs=[numpy.get_include()], extra_compile_args=["-O3", ]), 
]

setup(
    name = "sandbox",
    version = "0.1",
    author = "Charanpal Dhanjal ",
    author_email = "charanpal@gmail.com",
    description = ("A collection of machine learning algorithms"),
    license = "GPLv3",
    keywords = "numpy",
    url = "http://packages.python.org/sandbox",
    packages=['sandbox', 'sandbox.recommendation', 'sandbox.util',
    'sandbox.data'],
    install_requires=['numpy>=1.5.0', 'scipy>=0.7.1', "scikit-learn>=0.13"],
    long_description="A collection of machine learning algorithms",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License"
    ],  
    cmdclass = {'build_ext': build_ext},
  ext_modules = ext_modules
)
