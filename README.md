# FFI Navigator

Most modern IDEs support find function definition within the same language(e.g. python or c++).
However, it is very hard to do that for cross language FFI calls.
While solving this general problem can be very techinically challenging,
we can get around it by build a project specific analyzer that matches the
FFI registeration code patterns and recovers the necessary information.

This project is an example of that. Currently it supports the PackedFunc FFI in the Apache TVM project.
It is implemented as a [language server](https://microsoft.github.io/language-server-protocol/)
that provides getDefinition function for FFI calls and returns the location of the corresponding C++ API in the TVM project.
It complements the other more powerful languages servers that support navigation within the same language.


## Structure

- python/ffi_navigator The analysis code and language server
- vscode-extension language server extension for vscode

## Features

- Find definition/references of PackedFunc on the python and c++ side.
- Find definition/references of Object/Node on the python and c++ side.
  - move cursor to the object class name on the python side.
  - move cursor to the type key string on the c++ side.

These action works for a python symbol that refers a global PackedFunc(e.g. python/tvm/api.py:L59 `_api_internal._min_value`)
and function name strings that occur in `TVM_REGISTER_GLOBAL`, `@register_func` and `GetPackedFunc`.
Here are some examples you can try:

- python/tvm/api.py:L59 move cursor to `_api_internal._min_value` and run goto definition.
- src/relay/backend/compile_engine.cc:L728 `runtime::Registry::Get("relay.backend.lower")`,
  move cursor to the name and run goto definition.
- python/tvm/relay/expr.py:L191 move cursor to `Tuple` and run goto definition.
You can also try out find references in all these cases

## Installation

Install python package
```bash
pip install --user ffi-navigator
```

For developing the python package locally, we can just make sure ffi_navigator is in your python path in bashrc.
```bash
export PYTHONPATH=${PYTHONPATH}:/path/to/ffi-navigator/python
```
You can also directly install fft_navigator to system Python packages so that you don't need to setup PYTHONPATH.
Note that if you choose to install the package, you have to re-install it everytime you update the package.
```bash
python setup.py install
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

Set the project root to be ```/path/to/tvm``` using `M-x` `lsp-workspace-folders-add` `[RET]` `/path/to/tvm`
Try out the goto definition by opening a python file

- Move cursor to python/tvm/api.py line 59 `_api_internal._min_value`, type `M-x` `lsp-find-definition`

if you use eglot instead, check out [this PR](https://github.com/tqchen/ffi-navigator/pull/1).
eglot does not support multiple servers per language at the moment, the PR above contains a workaround.
