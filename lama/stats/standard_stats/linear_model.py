"""
The code to run linear models in R.

The current interface to R is to write binary files that R can read (numpy_to_dat). The reason r2py wasn't used is that
it used to be a pain to install. I imagine it's better now and using docker should improve things so adding
rp2y interface is on the todo list
"""


import subprocess as sub
import os
import struct
from pathlib import Path
import tempfile

from logzero import logger as logging
import numpy as np
import pandas as pd


from lama import common

LM_SCRIPT = common.lama_root_dir / 'stats' / 'rscripts' / 'lmFast.R'


def lm_r(data: pd.DataFrame, info:pd.DataFrame, plot_dir:Path=None, boxcox:bool=False, use_staging: bool=True) -> pd.DataFrame:
    """
    Fit multiple linear models and get the resulting p-values

    Parameters
    ----------
    df:
        columns:
            label_names + genotype and crl columns
        rows:
            specimens
    plot_dir
        where to optionally output lm plots (qq etc)
    boxcox
        whether to apply boxcox transformation to the dependent variable
    use_staging
        if true, uae staging as a fixed effect in the linear model

    Returns
    -------

    """
    input_binary_file = tempfile.NamedTemporaryFile().name
    line_level_pval_out_file = tempfile.NamedTemporaryFile().name
    line_level_tstat_out_file = tempfile.NamedTemporaryFile().name
    groups_file = tempfile.NamedTemporaryFile().name

    # create groups file
    if use_staging:
        groups = info[['genotype', 'staging']]
        formula = 'genotype,staging'

    else:
        groups = info[['genotype']]
        formula = 'genotype'


    groups.index.name = 'volume_id'
    groups.to_csv(groups_file)

    _numpy_to_dat(data, input_binary_file)

    cmd = ['Rscript',
           LM_SCRIPT,
           input_binary_file,
           groups_file,
           line_level_pval_out_file,
           line_level_tstat_out_file,
           formula,
           str(boxcox).upper(),  # bool to string for R
           ''  # No plots needed for permutation testing
           ]

    try:
        sub.call(cmd, stderr=sub.STDOUT)
    except (sub.CalledProcessError, Exception) as e:
        msg = "R linear model failed: {}".format(e.output)
        raise RuntimeError("R linear model failed: {}".format(msg))

    # Read in the pvalue and tvalue results. This will contain values from the line level call as well as
    # the speciemn-level calls and needs to be split accordingly
    try:
        p_all = np.fromfile(line_level_pval_out_file, dtype=np.float64).astype(np.float32)
        t_all = np.fromfile(line_level_tstat_out_file, dtype=np.float64).astype(np.float32)
    except FileNotFoundError as e:
        print(f'Linear model file from R not found {e}')
        raise

    os.remove(input_binary_file)
    os.remove(line_level_pval_out_file)
    os.remove(line_level_tstat_out_file)
    os.remove(groups_file)
    return p_all, t_all


def _numpy_to_dat(mat: np.ndarray, outfile: str):
    """
    Convert a numpy array to a binary file for reading in by R

    Parameters
    ----------
    mat: the data to be send to r
    outfile: the tem file name to store the binary file

    Notes
    -----
    DataFrame.values does not make a copy as np.arrar(df) does

    """
    # mat = mat.as_matrix()
    # create a binary file
    binfile = open(outfile, 'wb')
    # and write out two integers with the row and column dimension

    header = struct.pack('2I', mat.shape[0], mat.shape[1])
    binfile.write(header)
    # then loop over columns and write each
    for i in range(mat.shape[1]):
        data = struct.pack('%id' % mat.shape[0], *mat[:, i])
        binfile.write(data)

    binfile.close()
