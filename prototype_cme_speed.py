# -*- coding: utf-8 -*-
"""
===========================================
Drawing the AIA limb on a STEREO EUVI image
===========================================

In this example we use a STEREO-B and an SDO image to demonstrate how to
overplot the limb as seen by AIA on an EUVI-B image. Then we overplot the AIA
coordinate grid on the STEREO image.
"""
import numpy as np
import matplotlib.pyplot as plt

import astropy.units as u
from astropy.coordinates import SkyCoord

import sunpy.map
import sunpy.coordinates.wcs_utils
from sunpy.coordinates.frames import Helioprojective
from sunpy.net import Fido, attrs as a

from shapely.geometry import LineString, Point
from sympy import Point3D, Line3D

from matplotlib.lines import Line2D

import warnings
warnings.filterwarnings('ignore')

##############################################################################
# The first step is to download some data, we are going to get an image from
# early 2011 when the STEREO spacecraft were roughly 90 deg separated from the
# Earth.
stereo = (a.vso.Source('STEREO_B') &
          a.Instrument('EUVI') &
          a.Time('2011-01-01', '2011-01-01T00:10:00'))

aia = (a.Instrument('AIA') &
       a.vso.Sample(24 * u.hour) &
       a.Time('2011-01-01', '2011-01-02'))

wave = a.Wavelength(30 * u.nm, 31 * u.nm)
result = Fido.search(wave, aia | stereo)

###############################################################################
# Let's inspect the result
print(result)

##############################################################################
# and download the files
downloaded_files = Fido.fetch(result)
print(downloaded_files)

##############################################################################
# Let's create a dictionary with the two maps, which we crop to full disk.
maps = {m.name.split(' ', 1)[0]: m.submap(SkyCoord([-1100, 1100], [-1100, 1100],
                                                   unit=u.arcsec, frame=m.coordinate_frame))
        for m in sunpy.map.Map(downloaded_files)}

##############################################################################
# Next, let's calculate points on the limb in the AIA image for the half that
# can be seen from STEREO's point of view.

r = maps['AIA'].rsun_obs - 1 * u.arcsec  # remove one arcsec so it's on disk.
# Adjust the following range if you only want to plot on STEREO_A
th = np.linspace(-180 * u.deg, 0 * u.deg)
x = r * np.sin(th)
y = r * np.cos(th)
coords = SkyCoord(x, y, frame=maps['AIA'].coordinate_frame)


##############################################################################
# Now, let's plot both maps

fig = plt.figure(figsize=(10, 4))
ax1 = fig.add_subplot(1, 2, 1, projection=maps['AIA'])
maps['AIA'].plot(axes=ax1)
ax1_map_name = ax1.axes.title.get_text().split(' ', 1)[0]

ax2 = fig.add_subplot(1, 2, 2, projection=maps['EUVI-B'])
maps['EUVI-B'].plot(axes=ax2)

line_of_sight_is_defined = False


def onclick(event):
    global clicked_map, other_map, line_of_sight_is_defined
    clicked_map = which_map_clicked(event)
    other_map = which_is_other_map()
    clicked_skycoord = get_clicked_skycoord(event)
    draw_clicked_circle(clicked_skycoord)

    if not line_of_sight_is_defined:
        translate_skycoord_to_other_map(clicked_skycoord)
        draw_translated_line()
        line_of_sight_is_defined = True

    closeout_clicks(event)

    return True


def which_map_clicked(event):
    instrument_name = event.inaxes.title.get_text().split(' ', 1)[0]
    return instrument_name


def which_is_other_map():
    return np.setdiff1d(list(maps.keys()), [clicked_map])[0]


def get_clicked_skycoord(event):
    ix, iy = event.xdata, event.ydata
    clicked_skycoord = maps[clicked_map].pixel_to_world(ix * u.pix, iy * u.pix)
    return clicked_skycoord


def translate_skycoord_to_other_map(clicked_skycoord):
    global line_coords
    point_to_line = clicked_skycoord.realize_frame(clicked_skycoord.spherical * np.linspace(0.9, 1.1, 1e6) * u.AU)
    line_coords = point_to_line.transform_to(maps[other_map].coordinate_frame)


def draw_clicked_circle(clicked_skycoord):
    if ax1_map_name == clicked_map:
        ax1.plot_coord(clicked_skycoord, color='g', marker='o', fillstyle='none')
    else:
        ax2.plot_coord(clicked_skycoord, color='g', marker='o', fillstyle='none')


def draw_translated_line():
    if ax1_map_name == other_map:
        ax_lim = ax1.axis()
        ax1.plot_coord(line_coords, color='g', picker=5)
        ax1.axis(ax_lim)
    else:
        ax_lim = ax2.axis()
        ax2.plot_coord(line_coords, color='g', picker=5)
        ax2.axis(ax_lim)
    plt.draw()


def closeout_clicks(event):
    if line_of_sight_is_defined:
        fig.canvas.mpl_disconnect(cid1)


def pick_los_point(event):
    if isinstance(event.artist, Line2D):
        index = int(np.median(event.ind))
        skycoord_3d = line_coords[index]
        draw_3d_points(skycoord_3d)


def draw_3d_points(skycoord_3d):
    skycoord_3d_in_other_map = skycoord_3d.transform_to(maps[other_map].coordinate_frame)

    if ax1_map_name == other_map:
        ax2.plot_coord(skycoord_3d, color='blue', marker='o')
        ax1.plot_coord(skycoord_3d_in_other_map, color='blue', marker='o')
    else:
        ax1.plot_coord(skycoord_3d, color='blue', marker='o')
        ax2.plot_coord(skycoord_3d_in_other_map, color='blue', marker='o')

    plt.draw()


cid1 = fig.canvas.mpl_connect('button_press_event', onclick)
fig.canvas.mpl_connect('pick_event', pick_los_point)
plt.show()
