#!/usr/bin/env python

"""Tests for `aponeurosesdetection` package."""


import unittest
from click.testing import CliRunner

from aponeurosesdetection import aponeurosesdetection
from aponeurosesdetection import cli


class TestAponeurosesdetection(unittest.TestCase):
    """Tests for `aponeurosesdetection` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_something(self):
        """Test something."""
        'Opening of the image and color transform.'
        RGB_image = cv2.imread('cropped0.jpg', -1);
        gray_I = cv2.cvtColor(RGB_image, cv2.COLOR_RGB2GRAY);
        gray_I2 = 255 - gray_I; #inverse black and white

        'Multiscale Vessel Enhancement Method'
        seg, vesselness,hessXY, hessXX, hessYY = MVEF_2D(gray_I2, [4.], [0.5, 0.5]);

        'Rescale the pixels values if max. value is too low'
        maxi = np.max(seg);
        if maxi <=0.5 and maxi>0:
            seg = (seg/maxi)*255;

        'Visualization'
        cv2.imshow('MVEF',seg);
        cv2.imshow('Initial image', gray_I);
        cv2.imshow('Inverse image', gray_I2);
        cv2.waitKey(0) & 0xFF;
        cv2.destroyAllWindows();

    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 0
        assert 'aponeurosesdetection.cli.main' in result.output
        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert '--help  Show this message and exit.' in help_result.output
