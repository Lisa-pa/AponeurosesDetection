#!/usr/bin/env python

"""Tests for `SAMAE` package."""


import unittest
#from click.testing import CliRunner

#from SAMAE import SAMAE
#from SAMAE import cli




class TestAponeurosesdetection(unittest.TestCase):
    """Tests for `SAMAE` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

   

    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 0
        assert 'SAMAE.cli.main' in result.output
        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert '--help  Show this message and exit.' in help_result.output
