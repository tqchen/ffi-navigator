# TVM FFI Navigator

Toolkit that enhances IDEs to navigate ffi calls in the tvm project.

It contains a [language server](https://microsoft.github.io/language-server-protocol/) a vscode client.

## Structure

- python/tvm_ffi_navigator The analysis code and language server
- vscode-extension language server extension for vscode

## Installation

Install dependencies
```bash
pip install --user attrs python-jsonrpc-server``
```
Then we need to ake sure tvm_ffi_navigator is in your python path in bashrc.
```bash
export PYTHONPATH=${PYTHONPATH}:/path/to/tvm-ffi-navigator/python
```

### VSCode

See [vscode-extension](vscode-extension)

### Emacs

Install [lsp-mode](https://github.com/emacs-lsp/lsp-mode)

Add the following configuration
```el
(lsp-register-client
 (make-lsp-client
  :new-connection (lsp-stdio-connection '("python3" "-m" "tvm_ffi_navigator.langserver"))
  :major-modes '(python-mode c++-mode)
  :server-id 'tvm-ffi-navigator))
```

Set the project root to be ```/path/to/tvm``` using `M-x` `lsp-workspace-folders-add` `[RET]` `/path/to/tvm`
Try out the goto definition by opening a python file
- Move cursor to python/tvm/api.py line 59 `_api_internal._min_value`, type `M-x` `lsp-find-definition`
