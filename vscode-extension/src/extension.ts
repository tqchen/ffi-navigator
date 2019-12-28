/* --------------------------------------------------------------------------------------------
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 * ------------------------------------------------------------------------------------------ */

import * as path from 'path';
import { workspace, ExtensionContext } from 'vscode';

import {
	LanguageClient,
	LanguageClientOptions,
	ServerOptions,
	ExecutableOptions
} from 'vscode-languageclient';

let client: LanguageClient;

export function activate(context: ExtensionContext) {
	let pyCommand = 'python3'
 	let args = ['-m', 'ffi_navigator.langserver']
	let commandOptions: ExecutableOptions = { stdio: 'pipe', detached: false };
	let serverOptions: ServerOptions = {
		run: { command: pyCommand, args: args, options: commandOptions },
		debug: { command: pyCommand, args: args, options: commandOptions },
	};

	let clientOptions: LanguageClientOptions = {
		documentSelector: [
			{ scheme: 'file', language: 'python' },
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
