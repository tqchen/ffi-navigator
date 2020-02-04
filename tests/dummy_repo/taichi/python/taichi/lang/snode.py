class SNode:

  def loop_range(self):
    import taichi as ti
    return ti.Expr(ti.core.global_var_expr_from_snode(self.ptr))
