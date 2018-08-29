#!/usr/bin/python

"""
11/10/2017

Reruning the current lines with run_lama_stats.py bu using CRl as a fixed effect
lama_stats expects a config file
"""

from os.path import expanduser, join, dirname, isdir

home_dir = expanduser('~')
import sys
import yaml

sys.path.insert(0, join(dirname(__file__), '..'))
import run_lama_stats as stats
import common
import shutil

REL_PATH_TO_MUT_ORGAN_VOLS =  '../inverted_labels/organ_volumes_normed_to_mask_270818.csv'
REL_PATH_TO_WT_ORGAN_VOLS = '../../../../../output/wt_organ_vols_2708018.csv'

config_dict = {'data': {'organvolumes_280818_with_calibrated_p': {'mut': '../inverted_labels/similarity',
                                                'wt': '../../../../../output/inverted_labels/similarity',
                                                'wt_organ_vol_csv': REL_PATH_TO_WT_ORGAN_VOLS,
                                                'mut_organ_vol_csv': REL_PATH_TO_MUT_ORGAN_VOLS}},
               'fixed_mask': '../../../../../output/padded_target/mask_june_18.nrrd',
               'formulas': ['voxel ~ genotype + crl'],
               'label_map': '../../../../../output/padded_target/E14_5_atlas_v24_40.nrrd',
               'label_names':  '../../../../../output/padded_target/E14_5_atlas_v24_40_label_info.csv',
               'mut_staging_file': '../staging_info.csv',
               'n1': True,
               'voxel_size': 14.0,
               'wt_staging_file': '../../../../../output/staging_info.csv',
               'littermate_pattern': '_wt_',
               'use_auto_staging': False,
               'line_calibrated_p_values': '../../../../../output/padded_target/280818_line_level_p_thresholds.csv',
               'specimen_calibrated_p_values' : '../../../../../output/padded_target/280818_specimen_level_mutant_organ_p_threholds.csv'}

lines_list_path = join(home_dir, 'bit/LAMA_results/E14.5/paper_runs/mutant_runs/280618_analysed_lines/lines.csv')
root_dir = join(home_dir, 'bit/LAMA_results/E14.5/paper_runs/mutant_runs/280618_analysed_lines')
log_path = join(home_dir, 'bit/LAMA_results/E14.5/paper_runs/mutant_runs/270818_analysed_lines.log')


def run_stats(line_name):
    with open(log_path, 'a') as logger:
        config_dict['project_name'] = line_name

        if not isdir(join(root_dir, line)):
            print(f"skipping {line_name}")
            return

        outdir = join(root_dir, line_name, 'output', 'stats')

        if not isdir(outdir):
            common.mkdir_force(outdir)

        config_path = join(outdir, 'stats_organ_crl_280818.yaml')
        with open(config_path, 'w') as fh:
            fh.write(yaml.dump(config_dict))
        try:
            stats.run(config_path)
        except Exception as e:
            msg = '{} failed\n{}.'.format(line_name, e)
            print(msg)
            logger.write(msg)




lines = []
with open(lines_list_path, 'r') as fh:
    for line in fh:
        lines.append(line.strip())

for line in lines:
    print(('doing {}'.format(line)))
    run_stats(line)
