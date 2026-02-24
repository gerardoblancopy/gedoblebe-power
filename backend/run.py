#!/usr/bin/env python3
"""
Run the DC OPF Simulator Backend API server
"""
import os

# Fix for Apple Silicon/macOS OpenBLAS hanging inside scipy.optimize
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OPENBLAS_CORETYPE'] = 'HASWELL'

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
