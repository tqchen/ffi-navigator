import inspect
from .transformer import ASTTransformer
import ast
from .kernel_arguments import *
from .util import *

class Kernel:
  def materialize(self, key=None, args=None, arg_features=None):
    if key is None:
      key = (self.func, 0)
    if not self.runtime.materialized:
      self.runtime.materialize()
    if key in self.compiled_functions:
      return
    grad_suffix = ""
    if self.is_grad:
      grad_suffix = "_grad"
    kernel_name = "{}_c{}_{}_{}".format(self.func.__name__, self.kernel_counter, key[1], grad_suffix)
    import taichi as ti
    ti.info("Compiling kernel {}...".format(kernel_name))

    src = remove_indent(inspect.getsource(self.func))
    tree = ast.parse(src)
    if self.runtime.print_preprocessed:
      import astor
      print('Before preprocessing:')
      print(astor.to_source(tree.body[0]))

    func_body = tree.body[0]
    func_body.decorator_list = []

    local_vars = {}
    # Discussions: https://github.com/yuanming-hu/taichi/issues/282
    import copy
    global_vars = copy.copy(self.func.__globals__)

    for i, arg in enumerate(func_body.args.args):
      anno = arg.annotation
      if isinstance(anno, ast.Name):
        global_vars[anno.id] = self.arguments[i]

    visitor = ASTTransformer(
        excluded_paremeters=self.template_slot_locations,
        func=self,
        arg_features=arg_features)

    visitor.visit(tree)
    ast.fix_missing_locations(tree)

    if self.runtime.print_preprocessed:
      import astor
      print('After preprocessing:')
      print(astor.to_source(tree.body[0], indent_with='  '))

    ast.increment_lineno(tree, inspect.getsourcelines(self.func)[1] - 1)


    freevar_names = self.func.__code__.co_freevars
    closure = self.func.__closure__
    if closure:
      freevar_values = list(map(lambda x: x.cell_contents, closure))
      for name, value in zip(freevar_names, freevar_values):
        global_vars[name] = value

    # inject template parameters into globals
    for i in self.template_slot_locations:
      template_var_name = self.argument_names[i]
      global_vars[template_var_name] = args[i]

    exec(
        compile(tree, filename=inspect.getsourcefile(self.func), mode='exec'),
        global_vars, local_vars)
    compiled = local_vars[self.func.__name__]

    taichi_kernel = taichi_lang_core.create_kernel(kernel_name, self.is_grad)

    # Do not change the name of 'taichi_ast_generator'
    # The warning system needs this identifier to remove unnecessary messages
    def taichi_ast_generator():
      if self.runtime.inside_kernel:
        import taichi as ti
        raise ti.TaichiSyntaxError("Kernels cannot call other kernels. I.e., nested kernels are not allowed. Please check if you have direct/indirect invocation of kernels within kernels. Note that some methods provided by the Taichi standard library may invoke kernels, and please move their invocations to Python-scope.")
      self.runtime.inside_kernel = True
      compiled()
      self.runtime.inside_kernel = False

    taichi_kernel = taichi_kernel.define(taichi_ast_generator)

    assert key not in self.compiled_functions
    self.compiled_functions[key] = self.get_function_body(taichi_kernel)
