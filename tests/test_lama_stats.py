"""
Run all the config files in the test config directory
Currently just running and making sure there's no uncaught exceptions.
TODO: check that the correct output is generated too

To run these tests, the test data needs to be fechted from bit/dev/lama_stats_test_data
In future we should put this in a web-accessible place
"""
import shutil

from nose.tools import nottest, assert_equal

from lama_phenotype_detection.tests import (stats_config_dir, wt_registration_dir, mut_registration_dir, target_dir,
                                            stats_output_dir)
from lama_phenotype_detection.lama.stats.standard_stats import lama_stats_new

@nottest
def test_all():
    """
    Run the stats module. The data requirted for this to work must be initially made
    by running the test:  tests/test_lama.py:test_lama_job_runner()
    """

    config = stats_config_dir / 'new_stats_config.toml'
    lama_stats_new.run(config, wt_registration_dir, mut_registration_dir, stats_output_dir, target_dir)

# @nottest
def test_mutant_id_subset():
    """
    Thest whether specifying mutant id subset works
    """

    config = stats_config_dir / 'new_stats_config_test_mutant_id_subset.toml'
    lama_stats_new.run(config, wt_registration_dir, mut_registration_dir, stats_output_dir, target_dir)

@nottest
def test_specifiy_line():
    """
    Run the stats module. The data requirted for this to work must be initially made
    by running the test:  tests/test_lama.py:test_lama_job_runner()
    """
    line = 'mutant_1'  # Only run this line

    # Remove any previous output
    if stats_output_dir.is_dir():
        shutil.rmtree(stats_output_dir)

    config = stats_config_dir / 'new_stats_config.toml'
    lama_stats_new.run(config, wt_registration_dir, mut_registration_dir, stats_output_dir, target_dir, lines_to_process=[line])

    output_lines = [x.name for x in stats_output_dir.iterdir() if x.is_dir()]
    assert_equal([line],  output_lines)


@nottest
def test_erroneuos_configs():
    error_config_dir = stats_config_dir / 'erroneous_configs'

    for config in error_config_dir.iterdir():
        lama_stats_new.run(config, wt_registration_dir, mut_registration_dir, stats_output_dir, target_dir)

# @nottest
# def test_organ_vols():
#     config = join(CONFIG_DIR, 'organ_vols.yaml')
#     run_lama_stats.run(config)
#
# @nottest
# def test_glcm():
#     config = join(CONFIG_DIR, 'test_glcm.yaml')
#     run_lama_stats.run(config)
#
# @nottest
# def test_from_arbitrary_directory():
#     config = join(CONFIG_DIR, 'all_specimens.yaml')
#     os.chdir(os.path.expanduser('~'))
#     run_lama_stats.run(config)
#
# @nottest
# def test_missing_config():
#     config = join(CONFIG_DIR, 'all_specimens.flaml')
#     assert_raises(Exception, run_lama_stats.run, config)
#
# @nottest
# def test_misc():
#     config = join(CONFIG_DIR, 'misc_test.yaml')
#     run_lama_stats.run(config)
#
#
# @nottest
# def test_incorrect_staging_file():
#     pass

if __name__ == '__main__':
	test_all()
