# VS Code Extension for FFI Navigator

VSCode extension for ffi nagivator.


## Install the Extension to VSCode

### VSCode MarketPlace

You can get the extension by searching `FFI Navigator` in the VSCode marketplace.

### Build from Source

- Complete the python setup mentioned in the root's README. It is recommended to run the setup script; otherwise you have to make sure ffi_navigator is in PYTHONPATH when running VSCode.
- Run ```npm install && npm run compile```  on the vscode-extension folder
- Copy the extension folder to your vscode extension folder
  - ```cp -r /path/to/ffi-navigator/vscode-extension  ~/.vscode/extensions/ffi-navigator```
- Reload the window

## Install the Extension via Remote SSH

If you use VSCode Remote SSH extension to develop a project on a remote server, you can also enable ffi_navigator.

- Complete the above compile and intall steps on your local machine
- Open VSCode and connect to a remote server
- Go to the Extensions tab in VSCode and click "install" in "FFI Navigator" extension shown in "LOCAL - INSTALLED"
- You can now see "FFI Navigator" also appears at the "SSH: host - INSTALLED" side
- Complete the python setup mentioned in the root's README on the remote server
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

- You can select output tab in the terminal bar, and select `FFI Nagivator` to see logs from the python side
