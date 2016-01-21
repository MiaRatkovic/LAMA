#!/usr/bin/env python


import yaml
from os.path import relpath, join, dirname
import sys
import os
import SimpleITK as sitk
import numpy as np
import csv

from _phenotype_statistics import DeformationStats, GlcmStats, IntensityStats, JacobianStats, OrganVolumeStats
from _stats import TTest, LinearModelR

# Hack. Relative package imports won't work if this module is run as __main__
sys.path.insert(0, join(os.path.dirname(__file__), '..'))
import common
import gc
import logging
from invert import InvertVol

STATS_METHODS = {
    'lmR': LinearModelR,
    'ttest': TTest
}


class LamaStats(object):
    """
    Takes a stats.yaml config file and creates appropriate PhenotypeStatitics subclasses based on which analysis is to
    be performed
    """
    def __init__(self, config_path):
        self.config_dir = dirname(config_path)
        self.config_path = config_path
        self.config = self.get_config(config_path)
        self.setup_logging()
        self.mask_path = self.make_path(self.config['fixed_mask'])
        self.run_stats_from_config()

    def setup_logging(self):
        """
        If there is a log file specified in the config, use that path. Otherwise log to the stats folder
        """
        logpath = self.config.get('log')
        if not logpath:
            logpath = join(self.config_dir, 'stats.log')

        common.init_logging(logpath)
        logging.info('##### Stats started #####')
        logging.info(common.git_log())

    def make_path(self, path):
        """
        All paths are relative to the config file dir.
        Return relative paths to the config dir
        """
        return join(self.config_dir, path)

    def get_config(self, config_path):
        """
        Get the config and check for paths
        """
        with open(config_path) as fh:
            config = yaml.load(fh)
        try:
            data = config['data']
        except KeyError:
            raise Exception("stats config file need a 'data' entry")

        # wt_reg_norm = os.path.abspath(join(self.config_dir, reg_norm['wt']))
        # if not os.path.isdir(wt_reg_norm):
        #     raise OSError("cannot find wild type registered normalised directory: {}".format(wt_reg_norm))
        # mut_reg_norm = os.path.abspath(join(self.config_dir, reg_norm['mut']))
        # if not os.path.isdir(mut_reg_norm):
        #     raise OSError("cannot find mutant type registered normalised directory: {}".format(mut_reg_norm))

        return config

    def get_groups(self):
        """
        Combine group info from both the wildtype and mutants. Write out a combined groups csv file

        Returns
        -------
        None: if no file can be found
        Dict: Uf file can be found {volume_id: {groupname: grouptype, ...}...}
        """
        wt_g = self.config['wt_groups']
        mut_g = self.config['mut_groups']
        if not wt_g or not mut_g:
            return None

        wt_groups = join(self.config_dir, self.config['wt_groups'])
        mut_groups = join(self.config_dir, self.config['mut_groups'])

        if not os.path.isfile(wt_groups):
            logging
            print "Can't find the wild type groups file"
            return None

        if not os.path.isfile(mut_groups):
            print "Can't find the mutant groups file"
            return None

        # TODO: PUT SOME ERROR HANDLING IN IN CASE FILIES CAN'T BE FOUND ETC.
        combined_groups_file = os.path.abspath(join(self.config_dir, 'combined_groups.csv'))

        with open(wt_groups, 'r') as wr, open(mut_groups, 'r') as mr, open(combined_groups_file, 'w') as cw:
            reader = csv.reader(wr)
            first = True
            for row in reader:
                if first:
                    header = row
                    first = False
                    cw.write(','.join(header) + '\n')
                else:
                    cw.write(','.join(row) + '\n')

            reader_mut = csv.reader(mr)
            first = True
            for row in reader_mut:
                if first:
                    header_mut = row
                    if header != header_mut:
                        logging.warn("The header for mutant and wildtype group files is not identical")
                        print "The header for mutant and wildtype group files is not identical"
                        return None
                    first = False
                else:
                    cw.write(','.join(row) + '\n')
        return combined_groups_file

    def get_formulas(self):
        """
        Extract the linear/mixed model from the stasts config file. Just extract the independent varibale names for now

        Returns
        -------
        str: the independent variables/fixed effects
            or
        None: if no formulas can be found
        """
        parsed_formulas = []
        formulas = self.config.get('formulas')
        if not formulas:
            return None
        else:
            for formula_string in formulas:
                formula_elements = formula_string.split()[0::2][1:]  # extract all the effects, miss out the dependent variable
                parsed_formulas.append(','.join(formula_elements))
            return parsed_formulas

    def run_stats_from_config(self):
        """
        Build the regquired stats classes for each data type
        """

        mask = self.config.get('fixed_mask')
        if not mask:
            logging.warn('No mask specified in stats config file. Stats will take longer, and FDR correction might be too strict')
        fixed_mask = self.make_path(self.config.get('fixed_mask'))
        if not os.path.isfile(fixed_mask):
            logging.warn("Can't find mask {}. Stats will take longer, and FDR correction might be too strict".format(fixed_mask))
            fixed_mask = None

        voxel_size = self.config.get('voxel_size')
        if not voxel_size:
            voxel_size = 28.0
            logging.warn("Voxel size not set in config. Using a default of 28")
        voxel_size = float(voxel_size)

        groups = self.get_groups()
        formulas = self.get_formulas()
        project_name = self.config.get('project_name')
        if not project_name:
            project_name = '_'
        do_n1 = self.config.get('n1')

        mask_array = common.img_path_to_array(fixed_mask)
        mask_array_flat = mask_array.ravel().astype(np.bool)

        # loop over the types of data and do the required stats analysis
        for name, analysis_config in self.config['data'].iteritems():
            stats_tests = analysis_config['tests']
            mut_data_dir = self.make_path(analysis_config['mut'])
            wt_data_dir = self.make_path(analysis_config['wt'])
            outdir = join(self.config_dir, name)
            gc.collect()
            if name == 'registered_normalised':
                logging.info('#### doing intensity stats ####')
                int_stats = IntensityStats(outdir, wt_data_dir, mut_data_dir, project_name, mask_array_flat, groups, formulas, do_n1, voxel_size)
                for test in stats_tests:
                    int_stats.run(STATS_METHODS[test], name)
                del int_stats

            if name == 'jacobians':
                logging.info('#### doing jacobian stats ####')
                jac_stats = JacobianStats(outdir, wt_data_dir, mut_data_dir, project_name, mask_array_flat, groups, formulas, do_n1, voxel_size)
                for test in stats_tests:
                    jac_stats.run(STATS_METHODS[test], name)
                    # if invert_config:
                    #     jac_stats.invert(invert_config_path)
                del jac_stats

            if name == 'deformations':
                logging.info('#### doing deformation stats ####')
                def_stats = DeformationStats(outdir, wt_data_dir, mut_data_dir, project_name, mask_array_flat, groups, formulas, do_n1, voxel_size)
                for test in stats_tests:
                    def_stats.run(STATS_METHODS[test], name)
                    # if invert_config:
                    #     def_stats.invert(invert_config_path)
                del def_stats
            # if name == 'organ_volumes':
            #     vol_stats = OrganVolumeStats(outdir, wt_data_dir, mut_data_dir)
            #     for test in stats_tests:
            #         vol_stats.run(STATS_METHODS[test], name)

            if name == 'glcm':
                logging.info('#### doing GLCM texture stats ####')
                glcm_feature_types = analysis_config.get('glcm_feature_types')
                if not glcm_feature_types:
                    logging.warn("'glcm_feature_types' not specified in stats config file")
                    continue
                for feature_type in glcm_feature_types:
                    glcm_out_dir = join(outdir, feature_type)
                    wt_glcm_input_dir = join(wt_data_dir, feature_type)
                    mut_glcm_input_dir = join(mut_data_dir, feature_type)
                    glcm_stats = GlcmStats(glcm_out_dir, wt_glcm_input_dir, mut_glcm_input_dir, project_name, mask_array, groups, formulas, do_n1, voxel_size)
                    for test in stats_tests:
                        glcm_stats.run(STATS_METHODS[test], name)
                    del glcm_stats

        # We save the inversion until last as it may take a while and we may want to look at the raw resultsw first
        invert_config = self.config.get('invert_config_file')
        if invert_config:
            invert_config_path = self.make_path(invert_config)
            iv = InvertVol(invert_config_path, )


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser("Stats component of the phenotype detection pipeline")
    parser.add_argument('-c', '--config', dest='config', help='yaml config file contanign stats info', required=True)
    args = parser.parse_args()
    LamaStats(args.config)

