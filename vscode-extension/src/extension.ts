/* --------------------------------------------------------------------------------------------
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 * ------------------------------------------------------------------------------------------ */
import { ExtensionContext, window, workspace } from 'vscode';
import { execSync } from 'child_process';

import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
    ExecutableOptions
} from 'vscode-languageclient';

let client: LanguageClient;

export function activate(context: ExtensionContext) {
    // Check if the Python package is installed.
    try {
        execSync("pip3 show ffi_navigator");
    } catch (error) {
        window.showErrorMessage('ffi_navigator is not installed.' +
                                ' Please run "pip3 install ffi_navigator" and reload the window');
        return ;
    }
    const config = workspace.getConfiguration('')
    let pyCommand = config.get("ffi_navigator.pythonpath", "python")
    let args = ['-m', 'ffi_navigator.langserver']
    let commandOptions: ExecutableOptions = { stdio: 'pipe', detached: false };
    let serverOptions: ServerOptions = {
        run: { command: pyCommand, args: args, options: commandOptions },
        debug: { command: pyCommand, args: args, options: commandOptions },
    };

    let clientOptions: LanguageClientOptions = {
        documentSelector: [
            { scheme: 'file', language: 'python' },
            { scheme: 'file', language: 'cpp' },
            { scheme: 'file', language: 'c' },
            { scheme: 'file', language: 'plaintext' },
        ],
        synchronize: {
        }
    };
    client = new LanguageClient(
        'FFINavigator',
        'FFI Navigator',
        serverOptions,
        clientOptions
    );
    client.start();
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined;
    }
    return client.stop();
}
