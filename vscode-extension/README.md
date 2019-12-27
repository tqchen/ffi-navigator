# VS Code Extension for TVM FFI Navigator

VSCode extension for tvm ffi nagivator.


## Install the Extension to VSCode

- Install dependencies ```pip install --user attrs python-jsonrpc-server``
- Make sure tvm_ffi_navigator is in your python path in bashrc
  - ```export PYTHONPATH=${PYTHONPATH}:/path/to/tvm-ffi-navigator/python```
- Run ```npm install && npm run compile```  on the vscode-extension folder
- Copy the extension folder to your vscode extension folder
  - ```cp -r /path/to/tvm-ffi-navigator/vscode-extension  ~/.vscode/extensions/tvm-ffi-navigator```
- Reload the window


## Debug the Extension Client in VSCode Develop Mode

- Run ```npm install``` on the vscode-extension folder
- Open VS Code on the vscode-extension folder (do not include the python side)
- Press Debug -> Start Debugging
- Now VSCode will open a new window [Extension development host]
  - File-> Open/Open folder and select /path/to/tvm
  - Try out the goto definition by opening a python file, say python/tvm/api.py line 59 _api_internal._min_value, click goto definition

NOTE: You only need to reinstall the extension when the client side change.
- If you chane the python side, no re-installation is necessary.
- When you update the python project, and do some debugs, but remember to reload the window when you do so.

## Debug information from python package

- You can select output tab in the terminal bar, and select `TVM FFI Nagivator` to see logs from the python side




