/*!
 *  Copyright (c) 2018 by Contributors
 * \file graph/sampler.cc
 * \brief DGL sampler implementation
 */
#include <dgl/sampler.h>
#include <dgl/immutable_graph.h>
#include <dgl/runtime/container.h>
#include <dgl/packed_func_ext.h>
#include <dgl/random.h>
#include <dmlc/omp.h>
#include <algorithm>
#include <cstdlib>
#include <cmath>
#include <numeric>
#include "../c_api_common.h"
#include "../array/common.h"  // for ATEN_FLOAT_TYPE_SWITCH

using namespace dgl::runtime;

namespace dgl {

namespace {
/*
 * ArrayHeap is used to sample elements from vector
 */
template<typename ValueType>
class ArrayHeap {
 public:
  explicit ArrayHeap(const std::vector<ValueType>& prob) {
    vec_size_ = prob.size();
    bit_len_ = ceil(log2(vec_size_));
    limit_ = 1UL << bit_len_;
    // allocate twice the size
    heap_.resize(limit_ << 1, 0);
    // allocate the leaves
    for (size_t i = limit_; i < vec_size_+limit_; ++i) {
      heap_[i] = prob[i-limit_];
    }
    // iterate up the tree (this is O(m))
    for (int i = bit_len_-1; i >= 0; --i) {
      for (size_t j = (1UL << i); j < (1UL << (i + 1)); ++j) {
        heap_[j] = heap_[j << 1] + heap_[(j << 1) + 1];
      }
    }
  }
};

DGL_REGISTER_GLOBAL("nodeflow._CAPI_NodeFlowGetGraph")
.set_body([](DGLArgs args, DGLRetValue *rv) {
   NodeFlow nflow = args[0];
   *rv = nflow->graph;
});

DGL_REGISTER_GLOBAL("nodeflow._CAPI_NodeFlowGetNodeMapping")
.set_body([](DGLArgs args, DGLRetValue *rv) {
	    NodeFlow nflow = args[0];
   *rv = nflow->node_mapping;
});
} // namespace dgl
