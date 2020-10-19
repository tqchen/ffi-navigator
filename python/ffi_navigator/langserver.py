"""Language server using the navigator"""
import argparse
import logging
import pathlib
import attr
import os
import sys
from urllib.parse import urlparse, unquote
from . import workspace, pattern, lsp, util
from pyls_jsonrpc import dispatchers, endpoint, streams


def uri2path(uri):
    raw_path = unquote(urlparse(uri).path)
    if util.is_win():
        return str(pathlib.Path(raw_path[1:])) # workaround for path like /D:/...
    return raw_path

def path2uri(path):
    return pathlib.Path(os.path.abspath(path)).as_uri()

def pattern2loc(pattern_list):
    results = []
    dupset = set()
    proc = lambda decl: lsp.Location(uri=path2uri(decl.path), range=decl.range)
    for x in pattern_list:
        x = proc(x)
        key = attr.astuple(x)
        if key not in dupset:
            dupset.add(key)
            results.append(attr.asdict(x))
    return results


class BaseServer(dispatchers.MethodDispatcher):
    """Base language server can be used for unittesting."""
    def __init__(self):
        self.endpoint = None
        self.logger = logging
        self.ws = workspace.Workspace()

    def m_initialize(self, **kwargs):
        self.logger.info("Initialize %s", kwargs)
        rooturi = kwargs["rootUri"]
        if rooturi is not None:
            root_path = uri2path(kwargs["rootUri"])
            self.ws.initialize(root_path)
        return {
            "capabilities": {
                "definitionProvider": True,
                "referencesProvider": True,
            }
        }

    def m_initialized(self, **kwargs):
        pass

    def m_text_document__definition(self, **kwargs):
        path = uri2path(kwargs["textDocument"]["uri"])
        self.logger.info("textDocument/definition %s", kwargs)
        pos = lsp.Position(**kwargs["position"])
        source = open(path).readlines()
        sym = self.ws.extract_symbol(path, source, pos)

        if sym is None:
            self.logger.error("textDocument/definition cannot extract symbol, pos=%s, line=%s", pos, source[pos.line])
            return []
        if isinstance(sym, pattern.Symbol):
            res = self.ws.find_defs(path, sym.value)
        elif isinstance(sym, pattern.Ref):
            res = self.ws.key2defs.get(sym.key, [])
        else:
            return None
        res = pattern2loc(res)
        self.logger.info("textDocument/definition return %s", res)
        return res

    def m_text_document__references(self, **kwargs):
        path = uri2path(kwargs["textDocument"]["uri"])
        self.logger.info("textDocument/references %s", kwargs)
        pos = lsp.Position(**kwargs["position"])
        include_decl = kwargs.get("includeDeclaration", True)
        source = open(path).readlines()
        sym = self.ws.extract_symbol(path, source, pos)

        defs, refs = [], []
        if isinstance(sym, pattern.Symbol):
            defs = self.ws.find_defs(path, sym.value)
            if defs:
                refs = self.ws.find_refs(defs[0].key)
        elif isinstance(sym, pattern.Ref):
            if include_decl:
                defs = self.ws.key2defs.get(sym.key, [])
            refs = self.ws.find_refs(sym.key)
        elif isinstance(sym, pattern.Def):
            if include_decl:
                defs = [sym]
            refs = self.ws.find_refs(sym.key)
        else:
            self.logger.error("textDocument/references cannot extract symbol, pos=%s, line=%s", pos, source[pos.line])
            return []
        res = (pattern2loc(defs) if include_decl else []) + pattern2loc(refs)
        self.logger.info("textDocument/references return %s", res)
        return res


class StdIOServer(BaseServer):
    """The language server using stdio."""
    def __init__(self, ifile, ofile):
        super(StdIOServer, self).__init__()
        self._istream = streams.JsonRpcStreamReader(ifile)
        self._ostream = streams.JsonRpcStreamWriter(ofile)
        self.endpoint = endpoint.Endpoint(self, self._ostream.write)

    def run_ioloop(self):
        """Run the ioloop of the server by consuming inputs."""
        self._istream.listen(self.endpoint.consume)

    def m_exit(self):
        self.endpoint.shutdown()
        self._istream.close()
        self._ostream.close()


def main():
    StdIOServer(sys.stdin.buffer, sys.stdout.buffer).run_ioloop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(asctime)-15s] %(message)s")
    main()
