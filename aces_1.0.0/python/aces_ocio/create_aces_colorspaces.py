#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Implements support for *ACES* colorspaces conversions and transfer functions.
"""

import array
import math
import numpy
import os
import pprint

import PyOpenColorIO as ocio

import aces_ocio.generate_lut as genlut
from aces_ocio.generate_lut import (
    generate_1d_LUT_from_CTL,
    generate_3d_LUT_from_CTL,
    write_SPI_1d)
from aces_ocio.utilities import ColorSpace, mat44_from_mat33, sanitize_path, compact


__author__ = 'ACES Developers'
__copyright__ = 'Copyright (C) 2014 - 2015 - ACES Developers'
__license__ = ''
__maintainer__ = 'ACES Developers'
__email__ = 'aces@oscars.org'
__status__ = 'Production'

__all__ = ['create_ACEScc',
           'create_ACESproxy',
           'create_ACEScg',
           'create_ADX',
           'create_generic_log',
           'create_ACES_LMT',
           'create_lmts',
           'create_ACES_RRT_plus_ODT',
           'create_odts',
           'create_aces',
           'create_colorspaces']

# -------------------------------------------------------------------------
# *Matrices*
# -------------------------------------------------------------------------

# Matrix converting *ACES AP1* primaries to *AP0*.
ACES_AP1_to_AP0 = [0.6954522414, 0.1406786965, 0.1638690622,
                   0.0447945634, 0.8596711185, 0.0955343182,
                   -0.0055258826, 0.0040252103, 1.0015006723]

# Matrix converting *ACES AP0* primaries to *XYZ*.
ACES_AP0_to_XYZ = [0.9525523959, 0.0000000000, 0.0000936786,
                   0.3439664498, 0.7281660966, -0.0721325464,
                   0.0000000000, 0.0000000000, 1.0088251844]

# -------------------------------------------------------------------------
# *ACEScc*
# -------------------------------------------------------------------------
def create_ACEScc(aces_CTL_directory,
                  lut_directory, 
                  lut_resolution_1d,
                  cleanup,
                  name='ACEScc',
                  min_value=0.0,
                  max_value=1.0,
                  input_scale=1.0):
    cs = ColorSpace(name)
    cs.description = 'The %s color space' % name
    cs.aliases = ["acescc_ap1"]
    cs.equality_group = ''
    cs.family = 'ACES'
    cs.is_data = False

    ctls = [os.path.join(aces_CTL_directory,
                         'ACEScc',
                         'ACEScsc.ACEScc_to_ACES.a1.0.0.ctl'),
            # This transform gets back to the *AP1* primaries.
            # Useful as the 1d LUT is only covering the transfer function.
            # The primaries switch is covered by the matrix below:
            os.path.join(aces_CTL_directory,
                         'ACEScg',
                         'ACEScsc.ACES_to_ACEScg.a1.0.0.ctl')]
    lut = '%s_to_ACES.spi1d' % name

    lut = sanitize_path(lut)

    generate_1d_LUT_from_CTL(
        os.path.join(lut_directory, lut),
        ctls,
        lut_resolution_1d,
        'float',
        input_scale,
        1.0,
        {},
        cleanup,
        aces_CTL_directory,
        min_value,
        max_value)

    cs.to_reference_transforms = []
    cs.to_reference_transforms.append({
        'type': 'lutFile',
        'path': lut,
        'interpolation': 'linear',
        'direction': 'forward'})

    # *AP1* primaries to *AP0* primaries.
    cs.to_reference_transforms.append({
        'type': 'matrix',
        'matrix': mat44_from_mat33(ACES_AP1_to_AP0),
        'direction': 'forward'})

    cs.from_reference_transforms = []
    return cs


# -------------------------------------------------------------------------
# *ACESproxy*
# -------------------------------------------------------------------------
def create_ACESproxy(aces_CTL_directory,
                     lut_directory, 
                     lut_resolution_1d,
                     cleanup,
                     name='ACESproxy'):
    cs = ColorSpace(name)
    cs.description = 'The %s color space' % name
    cs.aliases = ["acesproxy_ap1"]
    cs.equality_group = ''
    cs.family = 'ACES'
    cs.is_data = False

    ctls = [os.path.join(aces_CTL_directory,
                         'ACESproxy',
                         'ACEScsc.ACESproxy10i_to_ACES.a1.0.0.ctl'),
            # This transform gets back to the *AP1* primaries.
            # Useful as the 1d LUT is only covering the transfer function.
            # The primaries switch is covered by the matrix below:
            os.path.join(aces_CTL_directory,
                         'ACEScg',
                         'ACEScsc.ACES_to_ACEScg.a1.0.0.ctl')]
    lut = '%s_to_aces.spi1d' % name

    lut = sanitize_path(lut)

    generate_1d_LUT_from_CTL(
        os.path.join(lut_directory, lut),
        ctls,
        lut_resolution_1d,
        'uint16',
        64.0,
        1.0,
        {},
        cleanup,
        aces_CTL_directory)

    cs.to_reference_transforms = []
    cs.to_reference_transforms.append({
        'type': 'lutFile',
        'path': lut,
        'interpolation': 'linear',
        'direction': 'forward'
    })

    # *AP1* primaries to *AP0* primaries.
    cs.to_reference_transforms.append({
        'type': 'matrix',
        'matrix': mat44_from_mat33(ACES_AP1_to_AP0),
        'direction': 'forward'
    })

    cs.from_reference_transforms = []
    return cs

# -------------------------------------------------------------------------
# *ACEScg*
# -------------------------------------------------------------------------
def create_ACEScg(aces_CTL_directory,
                  lut_directory, 
                  lut_resolution_1d,
                  cleanup,
                  name='ACEScg'):
    cs = ColorSpace(name)
    cs.description = 'The %s color space' % name
    cs.aliases = ["lin_ap1"]
    cs.equality_group = ''
    cs.family = 'ACES'
    cs.is_data = False

    cs.to_reference_transforms = []

    # *AP1* primaries to *AP0* primaries.
    cs.to_reference_transforms.append({
        'type': 'matrix',
        'matrix': mat44_from_mat33(ACES_AP1_to_AP0),
        'direction': 'forward'
    })

    cs.from_reference_transforms = []
    return cs

# -------------------------------------------------------------------------
# *ADX*
# -------------------------------------------------------------------------
def create_ADX(lut_directory, 
               lut_resolution_1d,
               bit_depth=10, 
               name='ADX'):
    name = '%s%s' % (name, bit_depth)
    cs = ColorSpace(name)
    cs.description = '%s color space - used for film scans' % name
    cs.aliases = ["adx%s" % str(bit_depth)]
    cs.equality_group = ''
    cs.family = 'ADX'
    cs.is_data = False

    if bit_depth == 10:
        cs.bit_depth = ocio.Constants.BIT_DEPTH_UINT10
        adx_to_cdd = [1023.0 / 500.0, 0.0, 0.0, 0.0,
                      0.0, 1023.0 / 500.0, 0.0, 0.0,
                      0.0, 0.0, 1023.0 / 500.0, 0.0,
                      0.0, 0.0, 0.0, 1.0]
        offset = [-95.0 / 500.0, -95.0 / 500.0, -95.0 / 500.0, 0.0]
    elif bit_depth == 16:
        cs.bit_depth = ocio.Constants.BIT_DEPTH_UINT16
        adx_to_cdd = [65535.0 / 8000.0, 0.0, 0.0, 0.0,
                      0.0, 65535.0 / 8000.0, 0.0, 0.0,
                      0.0, 0.0, 65535.0 / 8000.0, 0.0,
                      0.0, 0.0, 0.0, 1.0]
        offset = [-1520.0 / 8000.0, -1520.0 / 8000.0, -1520.0 / 8000.0,
                  0.0]

    cs.to_reference_transforms = []

    # Converting from *ADX* to *Channel-Dependent Density*.
    cs.to_reference_transforms.append({
        'type': 'matrix',
        'matrix': adx_to_cdd,
        'offset': offset,
        'direction': 'forward'})

    # Convert from Channel-Dependent Density to Channel-Independent Density
    cs.to_reference_transforms.append({
        'type': 'matrix',
        'matrix': [0.75573, 0.22197, 0.02230, 0,
                   0.05901, 0.96928, -0.02829, 0,
                   0.16134, 0.07406, 0.76460, 0,
                   0.0, 0.0, 0.0, 1.0],
        'direction': 'forward'})

    # Copied from *Alex Fry*'s *adx_cid_to_rle.py*
    def create_CID_to_RLE_LUT():

        def interpolate_1D(x, xp, fp):
            return numpy.interp(x, xp, fp)

        LUT_1D_xp = [-0.190000000000000,
                     0.010000000000000,
                     0.028000000000000,
                     0.054000000000000,
                     0.095000000000000,
                     0.145000000000000,
                     0.220000000000000,
                     0.300000000000000,
                     0.400000000000000,
                     0.500000000000000,
                     0.600000000000000]

        LUT_1D_fp = [-6.000000000000000,
                     -2.721718645000000,
                     -2.521718645000000,
                     -2.321718645000000,
                     -2.121718645000000,
                     -1.921718645000000,
                     -1.721718645000000,
                     -1.521718645000000,
                     -1.321718645000000,
                     -1.121718645000000,
                     -0.926545676714876]

        REF_PT = ((7120.0 - 1520.0) / 8000.0 * (100.0 / 55.0) -
                  math.log(0.18, 10.0))

        def cid_to_rle(x):
            if x <= 0.6:
                return interpolate_1D(x, LUT_1D_xp, LUT_1D_fp)
            return (100.0 / 55.0) * x - REF_PT

        def fit(value, from_min, from_max, to_min, to_max):
            if from_min == from_max:
                raise ValueError('from_min == from_max')
            return (value - from_min) / (from_max - from_min) * (
                to_max - to_min) + to_min

        NUM_SAMPLES = 2 ** 12
        RANGE = (-0.19, 3.0)
        data = []
        for i in xrange(NUM_SAMPLES):
            x = i / (NUM_SAMPLES - 1.0)
            x = fit(x, 0.0, 1.0, RANGE[0], RANGE[1])
            data.append(cid_to_rle(x))

        lut = 'ADX_CID_to_RLE.spi1d'
        write_SPI_1d(os.path.join(lut_directory, lut),
                     RANGE[0],
                     RANGE[1],
                     data,
                     NUM_SAMPLES, 1)

        return lut

    # Converting *Channel Independent Density* values to
    # *Relative Log Exposure* values.
    lut = create_CID_to_RLE_LUT()
    cs.to_reference_transforms.append({
        'type': 'lutFile',
        'path': lut,
        'interpolation': 'linear',
        'direction': 'forward'})

    # Converting *Relative Log Exposure* values to
    # *Relative Exposure* values.
    cs.to_reference_transforms.append({
        'type': 'log',
        'base': 10,
        'direction': 'inverse'})

    # Convert *Relative Exposure* values to *ACES* values.
    cs.to_reference_transforms.append({
        'type': 'matrix',
        'matrix': [0.72286, 0.12630, 0.15084, 0,
                   0.11923, 0.76418, 0.11659, 0,
                   0.01427, 0.08213, 0.90359, 0,
                   0.0, 0.0, 0.0, 1.0],
        'direction': 'forward'})

    cs.from_reference_transforms = []
    return cs

# -------------------------------------------------------------------------
# *Generic Log Transform*
# -------------------------------------------------------------------------
def create_generic_log(aces_CTL_directory,
                       lut_directory,
                       lut_resolution_1d,
                       cleanup,
                       name='log',
                       aliases=[],
                       min_value=0.0,
                       max_value=1.0,
                       input_scale=1.0,
                       middle_grey=0.18,
                       min_exposure=-6.0,
                       max_exposure=6.5):
    cs = ColorSpace(name)
    cs.description = 'The %s color space' % name
    cs.aliases = aliases
    cs.equality_group = name
    cs.family = 'Utility'
    cs.is_data = False

    ctls = [os.path.join(
        aces_CTL_directory,
        'utilities',
        'ACESlib.OCIO_shaper_log2_to_lin_param.a1.0.0.ctl')]
    lut = '%s_to_aces.spi1d' % name

    lut = sanitize_path(lut)

    generate_1d_LUT_from_CTL(
        os.path.join(lut_directory, lut),
        ctls,
        lut_resolution_1d,
        'float',
        input_scale,
        1.0,
        {'middleGrey': middle_grey,
         'minExposure': min_exposure,
         'maxExposure': max_exposure},
        cleanup,
        aces_CTL_directory,
        min_value,
        max_value)

    cs.to_reference_transforms = []
    cs.to_reference_transforms.append({
        'type': 'lutFile',
        'path': lut,
        'interpolation': 'linear',
        'direction': 'forward'})

    cs.from_reference_transforms = []
    return cs


# -------------------------------------------------------------------------
# *Individual LMTs*
# -------------------------------------------------------------------------
def create_ACES_LMT(lmt_name,
                    lmt_values,
                    shaper_info,
                    aces_CTL_directory,
                    lut_directory,
                    lut_resolution_1d=1024,
                    lut_resolution_3d=64,
                    cleanup=True,
                    aliases=[]):
    cs = ColorSpace('%s' % lmt_name)
    cs.description = 'The ACES Look Transform: %s' % lmt_name
    cs.aliases = aliases
    cs.equality_group = ''
    cs.family = 'Look'
    cs.is_data = False

    pprint.pprint(lmt_values)

    # Generating the *shaper* transform.
    (shaper_name,
     shaper_to_ACES_CTL,
     shaper_from_ACES_CTL,
     shaper_input_scale,
     shaper_params) = shaper_info

    shaper_lut = '%s_to_aces.spi1d' % shaper_name
    if not os.path.exists(os.path.join(lut_directory, shaper_lut)):
        ctls = [shaper_to_ACES_CTL % aces_CTL_directory]

        shaper_lut = sanitize_path(shaper_lut)

        generate_1d_LUT_from_CTL(
            os.path.join(lut_directory, shaper_lut),
            ctls,
            lut_resolution_1d,
            'float',
            1.0 / shaper_input_scale,
            1.0,
            shaper_params,
            cleanup,
            aces_CTL_directory)

    shaper_OCIO_transform = {
        'type': 'lutFile',
        'path': shaper_lut,
        'interpolation': 'linear',
        'direction': 'inverse'}

    # Generating the forward transform.
    cs.from_reference_transforms = []

    if 'transformCTL' in lmt_values:
        ctls = [shaper_to_ACES_CTL % aces_CTL_directory,
                os.path.join(aces_CTL_directory,
                             lmt_values['transformCTL'])]
        lut = '%s.%s.spi3d' % (shaper_name, lmt_name)

        lut = sanitize_path(lut)

        generate_3d_LUT_from_CTL(
            os.path.join(lut_directory, lut),
            ctls,
            lut_resolution_3d,
            'float',
            1.0 / shaper_input_scale,
            1.0,
            shaper_params,
            cleanup,
            aces_CTL_directory)

        cs.from_reference_transforms.append(shaper_OCIO_transform)
        cs.from_reference_transforms.append({
            'type': 'lutFile',
            'path': lut,
            'interpolation': 'tetrahedral',
            'direction': 'forward'
        })

    # Generating the inverse transform.
    cs.to_reference_transforms = []

    if 'transformCTLInverse' in lmt_values:
        ctls = [os.path.join(aces_CTL_directory,
                             odt_values['transformCTLInverse']),
                shaper_from_ACES_CTL % aces_CTL_directory]
        lut = 'Inverse.%s.%s.spi3d' % (odt_name, shaper_name)

        lut = sanitize_path(lut)

        generate_3d_LUT_from_CTL(
            os.path.join(lut_directory, lut),
            ctls,
            lut_resolution_3d,
            'half',
            1.0,
            shaper_input_scale,
            shaper_params,
            cleanup,
            aces_CTL_directory)

        cs.to_reference_transforms.append({
            'type': 'lutFile',
            'path': lut,
            'interpolation': 'tetrahedral',
            'direction': 'forward'})

        shaper_inverse = shaper_OCIO_transform.copy()
        shaper_inverse['direction'] = 'forward'
        cs.to_reference_transforms.append(shaper_inverse)

    return cs

# -------------------------------------------------------------------------
# *LMTs*
# -------------------------------------------------------------------------
def create_lmts(aces_CTL_directory,
                lut_directory, 
                lut_resolution_1d,
                lut_resolution_3d,
                lmt_info,
                shaper_name,
                cleanup):

    colorspaces = []

    # -------------------------------------------------------------------------
    # *LMT Shaper*
    # -------------------------------------------------------------------------
    lmt_lut_resolution_1d = max(4096, lut_resolution_1d)
    lmt_lut_resolution_3d = max(65, lut_resolution_3d)

    # Defining the *Log 2* shaper.
    lmt_shaper_name = 'LMT Shaper'
    lmt_shaper_name_aliases = ['crv_lmtshaper']
    lmt_params = {
        'middleGrey': 0.18,
        'minExposure': -10.0,
        'maxExposure': 6.5}

    lmt_shaper = create_generic_log(aces_CTL_directory,
                                    lut_directory,
                                    lmt_lut_resolution_1d,
                                    cleanup,
                                    name=lmt_shaper_name,
                                    middle_grey=lmt_params['middleGrey'],
                                    min_exposure=lmt_params['minExposure'],
                                    max_exposure=lmt_params['maxExposure'],
                                    aliases=lmt_shaper_name_aliases)
    colorspaces.append(lmt_shaper)

    shaper_input_scale_generic_log2 = 1.0

    # *Log 2* shaper name and *CTL* transforms bundled up.
    lmt_shaper_data = [
        lmt_shaper_name,
        os.path.join('%s',
                     'utilities',
                     'ACESlib.OCIO_shaper_log2_to_lin_param.a1.0.0.ctl'),
        os.path.join('%s',
                     'utilities',
                     'ACESlib.OCIO_shaper_lin_to_log2_param.a1.0.0.ctl'),
        shaper_input_scale_generic_log2,
        lmt_params]

    sorted_LMTs = sorted(lmt_info.iteritems(), key=lambda x: x[1])
    print(sorted_LMTs)
    for lmt in sorted_LMTs:
        (lmt_name, lmt_values) = lmt
        lmt_aliases = ["look_%s" % compact(lmt_values['transformUserName'])]
        cs = create_ACES_LMT(
            lmt_values['transformUserName'],
            lmt_values,
            lmt_shaper_data,
            aces_CTL_directory,
            lut_directory,
            lmt_lut_resolution_1d,
            lmt_lut_resolution_3d,
            cleanup,
            lmt_aliases)
        colorspaces.append(cs)

    return colorspaces

# -------------------------------------------------------------------------
# *ACES RRT* with supplied *ODT*.
# -------------------------------------------------------------------------
def create_ACES_RRT_plus_ODT(odt_name,
                             odt_values,
                             shaper_info,
                             aces_CTL_directory,
                             lut_directory,
                             lut_resolution_1d=1024,
                             lut_resolution_3d=64,
                             cleanup=True,
                             aliases=[]):
    cs = ColorSpace('%s' % odt_name)
    cs.description = '%s - %s Output Transform' % (
        odt_values['transformUserNamePrefix'], odt_name)
    cs.aliases = aliases
    cs.equality_group = ''
    cs.family = 'Output'
    cs.is_data = False

    pprint.pprint(odt_values)

    # Generating the *shaper* transform.
    (shaper_name,
     shaper_to_ACES_CTL,
     shaper_from_ACES_CTL,
     shaper_input_scale,
     shaper_params) = shaper_info

    if 'legalRange' in odt_values:
        shaper_params['legalRange'] = odt_values['legalRange']
    else:
        shaper_params['legalRange'] = 0

    shaper_lut = '%s_to_aces.spi1d' % shaper_name
    if not os.path.exists(os.path.join(lut_directory, shaper_lut)):
        ctls = [shaper_to_ACES_CTL % aces_CTL_directory]

        shaper_lut = sanitize_path(shaper_lut)

        generate_1d_LUT_from_CTL(
            os.path.join(lut_directory, shaper_lut),
            ctls,
            lut_resolution_1d,
            'float',
            1.0 / shaper_input_scale,
            1.0,
            shaper_params,
            cleanup,
            aces_CTL_directory)

    shaper_OCIO_transform = {
        'type': 'lutFile',
        'path': shaper_lut,
        'interpolation': 'linear',
        'direction': 'inverse'}

    # Generating the *forward* transform.
    cs.from_reference_transforms = []

    if 'transformLUT' in odt_values:
        transform_LUT_file_name = os.path.basename(
            odt_values['transformLUT'])
        lut = os.path.join(lut_directory, transform_LUT_file_name)
        shutil.copy(odt_values['transformLUT'], lut)

        cs.from_reference_transforms.append(shaper_OCIO_transform)
        cs.from_reference_transforms.append({
            'type': 'lutFile',
            'path': transform_LUT_file_name,
            'interpolation': 'tetrahedral',
            'direction': 'forward'})
    elif 'transformCTL' in odt_values:
        ctls = [
            shaper_to_ACES_CTL % aces_CTL_directory,
            os.path.join(aces_CTL_directory,
                         'rrt',
                         'RRT.a1.0.0.ctl'),
            os.path.join(aces_CTL_directory,
                         'odt',
                         odt_values['transformCTL'])]
        lut = '%s.RRT.a1.0.0.%s.spi3d' % (shaper_name, odt_name)

        lut = sanitize_path(lut)

        generate_3d_LUT_from_CTL(
            os.path.join(lut_directory, lut),
            # shaperLUT,
            ctls,
            lut_resolution_3d,
            'float',
            1.0 / shaper_input_scale,
            1.0,
            shaper_params,
            cleanup,
            aces_CTL_directory)

        cs.from_reference_transforms.append(shaper_OCIO_transform)
        cs.from_reference_transforms.append({
            'type': 'lutFile',
            'path': lut,
            'interpolation': 'tetrahedral',
            'direction': 'forward'})

    # Generating the *inverse* transform.
    cs.to_reference_transforms = []

    if 'transformLUTInverse' in odt_values:
        transform_LUT_inverse_file_name = os.path.basename(
            odt_values['transformLUTInverse'])
        lut = os.path.join(lut_directory, transform_LUT_inverse_file_name)
        shutil.copy(odt_values['transformLUTInverse'], lut)

        cs.to_reference_transforms.append({
            'type': 'lutFile',
            'path': transform_LUT_inverse_file_name,
            'interpolation': 'tetrahedral',
            'direction': 'forward'})

        shaper_inverse = shaper_OCIO_transform.copy()
        shaper_inverse['direction'] = 'forward'
        cs.to_reference_transforms.append(shaper_inverse)
    elif 'transformCTLInverse' in odt_values:
        ctls = [os.path.join(aces_CTL_directory,
                             'odt',
                             odt_values['transformCTLInverse']),
                os.path.join(aces_CTL_directory,
                             'rrt',
                             'InvRRT.a1.0.0.ctl'),
                shaper_from_ACES_CTL % aces_CTL_directory]
        lut = 'InvRRT.a1.0.0.%s.%s.spi3d' % (odt_name, shaper_name)

        lut = sanitize_path(lut)

        generate_3d_LUT_from_CTL(
            os.path.join(lut_directory, lut),
            # None,
            ctls,
            lut_resolution_3d,
            'half',
            1.0,
            shaper_input_scale,
            shaper_params,
            cleanup,
            aces_CTL_directory)

        cs.to_reference_transforms.append({
            'type': 'lutFile',
            'path': lut,
            'interpolation': 'tetrahedral',
            'direction': 'forward'})

        shaper_inverse = shaper_OCIO_transform.copy()
        shaper_inverse['direction'] = 'forward'
        cs.to_reference_transforms.append(shaper_inverse)

    return cs

# -------------------------------------------------------------------------
# *ODTs*
# -------------------------------------------------------------------------
def create_odts(aces_CTL_directory,
                lut_directory, 
                lut_resolution_1d,
                lut_resolution_3d,
                odt_info,
                shaper_name,
                cleanup,
                linear_display_space,
                log_display_space):

    colorspaces = []
    displays = {}

    # -------------------------------------------------------------------------
    # *RRT / ODT* Shaper Options
    # -------------------------------------------------------------------------
    shaper_data = {}

    # Defining the *Log 2* shaper.
    log2_shaper_name = shaper_name
    log2_shaper_name_aliases = ["crv_%s" % compact(shaper_name)]
    log2_params = {
        'middleGrey': 0.18,
        'minExposure': -6.0,
        'maxExposure': 6.5}

    log2_shaper = create_generic_log(
        aces_CTL_directory,
        lut_directory,
        lut_resolution_1d,
        cleanup,
        name=log2_shaper_name,
        middle_grey=log2_params['middleGrey'],
        min_exposure=log2_params['minExposure'],
        max_exposure=log2_params['maxExposure'],
        aliases=log2_shaper_name_aliases)
    colorspaces.append(log2_shaper)

    shaper_input_scale_generic_log2 = 1.0

    # *Log 2* shaper name and *CTL* transforms bundled up.
    log2_shaper_data = [
        log2_shaper_name,
        os.path.join('%s',
                     'utilities',
                     'ACESlib.OCIO_shaper_log2_to_lin_param.a1.0.0.ctl'),
        os.path.join('%s',
                     'utilities',
                     'ACESlib.OCIO_shaper_lin_to_log2_param.a1.0.0.ctl'),
        shaper_input_scale_generic_log2,
        log2_params]

    shaper_data[log2_shaper_name] = log2_shaper_data

    # Shaper that also includes the AP1 primaries.
    # Needed for some LUT baking steps.
    log2_shaper_api1_name_aliases = ["%s_ap1" % compact(shaper_name)]
    log2_shaper_AP1 = create_generic_log(
        aces_CTL_directory,
        lut_directory,
        lut_resolution_1d,
        cleanup,
        name=log2_shaper_name,
        middle_grey=log2_params['middleGrey'],
        min_exposure=log2_params['minExposure'],
        max_exposure=log2_params['maxExposure'],
        aliases=log2_shaper_api1_name_aliases)
    log2_shaper_AP1.name = '%s - AP1' % log2_shaper_AP1.name

    # *AP1* primaries to *AP0* primaries.
    log2_shaper_AP1.to_reference_transforms.append({
        'type': 'matrix',
        'matrix': mat44_from_mat33(ACES_AP1_to_AP0),
        'direction': 'forward'
    })
    colorspaces.append(log2_shaper_AP1)

    rrt_shaper = log2_shaper_data

    # *RRT + ODT* combinations.
    sorted_odts = sorted(odt_info.iteritems(), key=lambda x: x[1])
    print(sorted_odts)
    for odt in sorted_odts:
        (odt_name, odt_values) = odt

        # Handling *ODTs* that can generate either *legal* or *full* output.
        if odt_name in ['Academy.Rec2020_100nits_dim.a1.0.0',
                        'Academy.Rec709_100nits_dim.a1.0.0',
                        'Academy.Rec709_D60sim_100nits_dim.a1.0.0']:
            odt_name_legal = '%s - Legal' % odt_values['transformUserName']
        else:
            odt_name_legal = odt_values['transformUserName']

        odt_legal = odt_values.copy()
        odt_legal['legalRange'] = 1

        odt_aliases = ["out_%s" % compact(odt_name_legal)]

        cs = create_ACES_RRT_plus_ODT(
            odt_name_legal,
            odt_legal,
            rrt_shaper,
            aces_CTL_directory,
            lut_directory,
            lut_resolution_1d,
            lut_resolution_3d,
            cleanup,
            odt_aliases)
        colorspaces.append(cs)

        displays[odt_name_legal] = {
            'Linear': linear_display_space,
            'Log': log_display_space,
            'Output Transform': cs}

        if odt_name in ['Academy.Rec2020_100nits_dim.a1.0.0',
                        'Academy.Rec709_100nits_dim.a1.0.0',
                        'Academy.Rec709_D60sim_100nits_dim.a1.0.0']:
            print('Generating full range ODT for %s' % odt_name)

            odt_name_full = '%s - Full' % odt_values['transformUserName']
            odt_full = odt_values.copy()
            odt_full['legalRange'] = 0

            odt_full_aliases = ["out_%s" % compact(odt_name_full)]

            cs_full = create_ACES_RRT_plus_ODT(
                odt_name_full,
                odt_full,
                rrt_shaper,
                aces_CTL_directory,
                lut_directory,
                lut_resolution_1d,
                lut_resolution_3d,
                cleanup,
                odt_full_aliases)
            colorspaces.append(cs_full)

            displays[odt_name_full] = {
                'Linear': linear_display_space,
                'Log': log_display_space,
                'Output Transform': cs_full}

    return (colorspaces, displays)

def create_aces():
    # Defining the reference colorspace.
    ACES = ColorSpace('ACES2065-1')
    ACES.description = (
        'The Academy Color Encoding System reference color space')
    ACES.equality_group = ''
    ACES.aliases = ["lin_ap0", "aces"]
    ACES.family = 'ACES'
    ACES.is_data = False
    ACES.allocation_type = ocio.Constants.ALLOCATION_LG2
    ACES.allocation_vars = [-15, 6]

    return ACES

def create_colorspaces(aces_CTL_directory, 
                       lut_directory, 
                       lut_resolution_1d, 
                       lut_resolution_3d,
                       lmt_info,
                       odt_info,
                       shaper_name,
                       cleanup):
    """
    Generates the colorspace conversions.

    Parameters
    ----------
    parameter : type
        Parameter description.

    Returns
    -------
    type
         Return value description.
    """

    colorspaces = []

    ACES = create_aces()

    ACEScc = create_ACEScc(aces_CTL_directory, lut_directory, lut_resolution_1d, cleanup)
    colorspaces.append(ACEScc)

    ACESproxy = create_ACESproxy(aces_CTL_directory, lut_directory, lut_resolution_1d, cleanup)
    colorspaces.append(ACESproxy)

    ACEScg = create_ACEScg(aces_CTL_directory, lut_directory, lut_resolution_1d, cleanup)
    colorspaces.append(ACEScg)

    ADX10 = create_ADX(lut_directory, lut_resolution_1d, bit_depth=10)
    colorspaces.append(ADX10)

    ADX16 = create_ADX(lut_directory, lut_resolution_1d, bit_depth=16)
    colorspaces.append(ADX16)

    lmts = create_lmts(aces_CTL_directory, 
                       lut_directory, 
                       lut_resolution_1d, 
                       lut_resolution_3d,
                       lmt_info,
                       shaper_name,
                       cleanup)
    colorspaces.extend(lmts)

    (odts, displays) = create_odts(aces_CTL_directory, 
                                   lut_directory, 
                                   lut_resolution_1d, 
                                   lut_resolution_3d,
                                   odt_info,
                                   shaper_name,
                                   cleanup,
                                   ACES,
                                   ACEScc)
    colorspaces.extend(odts)

    return (ACES, colorspaces, displays, ACEScc)
