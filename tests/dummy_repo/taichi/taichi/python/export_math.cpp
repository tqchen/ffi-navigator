/*******************************************************************************
    Copyright (c) The Taichi Authors (2016- ). All Rights Reserved.
    The use of this software is governed by the LICENSE file.
*******************************************************************************/

#include <taichi/python/export.h>
#include <taichi/common/dict.h>
#include <taichi/visualization/rgb.h>
#include <taichi/image/operations.h>

void export_math(py::module &m) {

  py::class_<Array2D<Vector4>>(m, "Array2DVector4")
      .def(py::init<Vector2i, Vector4>())
      .def("get_width", &Array2D<Vector4>::get_width)
      .def("get_height", &Array2D<Vector4>::get_height)
      .def("get_channels", &return_constant<Array2D<Vector4>, 4>)
      .def("write", &Array2D<Vector4>::write_as_image)
      .def("from_ndarray", &ndarray_to_image_buffer<Array2D<Vector4>, 4>)
      .def("write_to_disk", &Array2D<Vector4>::write_to_disk)
      .def("read_from_disk", &Array2D<Vector4>::read_from_disk)
      .def("rasterize", &Array2D<Vector4>::rasterize)
      .def("rasterize_scale", &Array2D<Vector4>::rasterize_scale)
      .def("to_ndarray", &array2d_to_ndarray<Array2D<Vector4>, 4>);
}
