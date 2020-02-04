import sys
import datetime
import platform
import random
import taichi
import time


def array2d_to_image(arr,
                     width,
                     height,
                     color_255=None,
                     transform='levelset',
                     alpha_scale=1.0):
  from taichi import tc_core
  if color_255 is None:
    assert isinstance(arr, tc_core.Array2DVector3) or isinstance(
        arr, tc_core.Array2DVector4)
  import pyglet
  rasterized = arr.rasterize(width, height)
  raw_data = np.empty((width, height, arr.get_channels()), dtype=np.float32)
  rasterized.to_ndarray(raw_data.ctypes.data_as(ctypes.c_void_p).value)
  if transform == 'levelset':
    raw_data = (raw_data <= 0).astype(np.float32)
  else:
    x0, x1 = transform
    raw_data = (np.clip(raw_data, x0, x1) - x0) / (x1 - x0)
  raw_data = raw_data.swapaxes(0, 1).copy()
  if isinstance(arr, tc_core.Array2DVector3):
    dat = np.stack(
        [raw_data,
         np.ones(shape=(width, height, 1), dtype=np.float32)],
        axis=2).flatten().reshape((height * width, 4))
    dat = dat * 255.0
  elif isinstance(arr, tc_core.Array2DVector4):
    dat = raw_data.flatten().reshape((height * width, 4))
    dat = dat * 255.0
  else:
    raw_data = raw_data.flatten()
    dat = np.outer(np.ones_like(raw_data), color_255)
    dat[:, 3] = (color_255[3] * raw_data)
  dat[:, 3] *= alpha_scale
  dat = np.clip(dat, 0.0, 255.0)
  dat = dat.astype(np.uint8)
  assert dat.shape == (height * width, 4)
  image_data = pyglet.image.ImageData(width, height, 'RGBA', dat.tostring())
  return image_data
