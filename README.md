# FFI Navigator

[![Build Status](https://dev.azure.com/ffi-navigator/ffi-navigator/_apis/build/status/tqchen.ffi-navigator?branchName=master)](https://dev.azure.com/ffi-navigator/ffi-navigator/_build/latest?definitionId=1&branchName=master)

Most modern IDEs support find function definition within the same language(e.g. python or c++). However, it is very hard to do that for cross-language FFI calls. While solving this general problem can be very technically challenging, we can get around it by building a project-specific analyzer that matches the FFI registration code patterns and recovers the necessary information.

This project is an example of that. Currently, it supports the PackedFunc FFI in the Apache TVM project. It is implemented as a [language server](https://microsoft.github.io/language-server-protocol/) that provides getDefinition function for FFI calls and returns the location of the corresponding C++ API in the TVM project. It complements the IDE tools that support navigation within the same language. We also have preliminary support for MXNet, DGL, and PyTorch, so we can do goto-definition from Python to C++ in these projects too.


## Installation

Install python package
```bash
pip install --user ffi-navigator
```

### VSCode

See [vscode-extension](vscode-extension)

### Emacs

Install [lsp-mode](https://github.com/emacs-lsp/lsp-mode)

Add the following configuration
```el
(lsp-register-client
 (make-lsp-client
  :new-connection (lsp-stdio-connection '("python3" "-m" "ffi_navigator.langserver"))
  :major-modes '(python-mode c++-mode)
  :server-id 'ffi-navigator
  :add-on? t))
```

- Use commands like `M-x` `lsp-find-definition` and `M-x` `lsp-find-references`

If you use eglot instead, check out [this PR](https://github.com/tqchen/ffi-navigator/pull/1).
eglot does not support multiple servers per language at the moment, the PR above contains a workaround.


## Features

### TVM FFI

- Find definition/references of FFI objects(e.g. PackedFunc in TVM) on the python and c++ side.
  - Jump from a python PackedFunc into ```TVM_REGISTER_GLOBAL```, ```@register_func```
- Find definition/references of FFI objects on the python and c++ side.
  - move cursor to the object class name on the python side.
  - move cursor to the ```_type_key``` string on the c++ side.

### PyTorch

- Jump to C10 registered ops. In python they corresponds to functions under `torch.ops` namespace.
  - Example: `torch.ops.quantized.conv2d (py)` -> `c10::RegisterOperators().op("quantized::conv2d", ...) (cpp)`
- Jump to cpp functions wrapped by pybind.
  - Example: `torch._C._jit_script_class_compile (py)` -> `m.def( "_jit_script_class_compile", ...) (cpp)`


## Development

For developing the python package locally, we can just make sure ffi_navigator is in your python path in bashrc.
```bash
export PYTHONPATH=${PYTHONPATH}:/path/to/ffi-navigator/python
```

### Project Structure

- python/ffi_navigator The analysis code and language server
- python/ffi_navigator/dialect Per project dialects
- vscode-extension language server extension for vscode

### Adding Support for New FFI Patterns

Add your FFI convention to [dialect namespace](python/ffi_navigator/dialect).


## Demo

### VSCode

See [vscode-extension](vscode-extension)

### Emacs

#### Goto definition from Python to C++
![goto-def-py-cpp](https://github.com/tvmai/web-data/blob/master/images/ffi-navigator/emacs/tvm_find_def_py_cpp.gif)
#### Goto definition from C++ to Python
![goto-def-py-cpp](https://github.com/tvmai/web-data/blob/master/images/ffi-navigator/emacs/tvm_find_def_cpp_py.gif)
#### Find reference across Python and C++
![goto-def-py-cpp](https://github.com/tvmai/web-data/blob/master/images/ffi-navigator/emacs/tvm_find_reference.gif)
#### Goto definition in PyTorch
![goto-def-py-cpp](https://github.com/tvmai/web-data/blob/master/images/ffi-navigator/emacs/torch.gif)
