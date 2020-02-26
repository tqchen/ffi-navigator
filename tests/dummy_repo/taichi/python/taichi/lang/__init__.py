from .impl import *
from .matrix import Matrix
from .transformer import TaichiSyntaxError
from .ndrange import ndrange, GroupedNDRange

core = taichi_lang_core
cfg = default_cfg()
current_cfg = current_cfg()
x86_64 = core.x86_64
cuda = core.cuda
profiler_print = lambda: core.get_current_program().profiler_print()
profiler_clear = lambda: core.get_current_program().profiler_clear()


def cache_shared(v):
  taichi_lang_core.cache(0, v.ptr)


def cache_l1(v):
  taichi_lang_core.cache(1, v.ptr)


parallelize = core.parallelize
serialize = lambda: parallelize(1)
vectorize = core.vectorize
block_dim = core.block_dim
cache = core.cache
