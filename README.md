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

## Installation

Install dependencies
```bash
pip install --user attrs python-jsonrpc-server``
```
Then we need to ake sure ffi_navigator is in your python path in bashrc.
```bash
export PYTHONPATH=${PYTHONPATH}:/path/to/ffi-navigator/python
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
