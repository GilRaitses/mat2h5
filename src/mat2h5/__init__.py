"""
mat2h5 - MATLAB to H5 Conversion Tool

A standalone tool for converting MAGAT (MATLAB Track Analysis) experiment data
to H5 format for use in Python analysis pipelines.
"""

__version__ = "1.0.0"
__author__ = "INDYsim Contributors"

from .bridge import MAGATBridge

__all__ = ['MAGATBridge']

