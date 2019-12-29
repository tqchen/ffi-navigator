"""Language server using the navigator"""
import argparse
import logging
import pathlib
import attr
import os
import sys
from urllib.parse import urlparse
from . import workspace, pattern, lsp
from pyls_jsonrpc import dispatchers, endpoint, streams


def uri2path(uri):
    return urlparse(uri).path

def path2uri(path):
    return pathlib.Path(os.path.abspath(path)).as_uri()

def def2loc(packed_def_list):
    proc = lambda decl: attr.asdict(lsp.Location(uri=path2uri(decl.path), range=decl.range))
    return [proc(x) for x in packed_def_list]


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
        logging.info("textDocument/definition %s", kwargs)
        pos = lsp.Position(**kwargs["position"])
        source = open(path).readlines()
        sym = pattern.extract_symbol(source, pos)

        if isinstance(sym, pattern.SymExpr):
            res = self.ws.find_definition(path, sym.value)
        elif isinstance(sym, pattern.SymGetPackedFunc):
            res = self.ws.get_packed_def(sym.value)
        elif isinstance(sym, pattern.SymRegObject):
            res = self.ws._object_defs.get(sym.value, [])
        else:
            logging.error("textDocument/definition cannot extract symbol, pos=%s, line=%s", pos, source[pos.line])
            return []
        res = def2loc(res)
        logging.info("textDocument/definition return %s", res)
        return res

    def m_text_document__references(self, **kwargs):
        path = uri2path(kwargs["textDocument"]["uri"])
        logging.info("textDocument/references %s", kwargs)
        pos = lsp.Position(**kwargs["position"])
        include_decl = kwargs.get("includeDeclaration", True)
        source = open(path).readlines()
        sym = pattern.extract_symbol(source, pos)
        defs, refs = [], []

        if isinstance(sym, pattern.SymExpr):
            defs = self.ws.find_definition(path, sym.value)
            if defs:
                refs = self.ws.find_packed_refs(defs[0].full_name)
        elif isinstance(sym, pattern.SymGetPackedFunc):
            if include_decl:
                defs = self.ws.get_packed_def(sym.value)
            refs = self.ws.find_packed_refs(sym.value)
        elif isinstance(sym, pattern.SymRegPackedFunc):
            if include_decl:
                defs = self.ws.get_packed_def(sym.value)
            refs = self.ws.find_packed_refs(sym.value)
        elif isinstance(sym, (pattern.SymRegObject, pattern.SymDeclObject)):
            if include_decl:
                defs = self.ws._object_defs.get(sym.value, [])
            refs = self.ws._object_regs.get(sym.value, [])
        else:
            logging.error("textDocument/references cannot extract symbol, pos=%s, line=%s", pos, source[pos.line])
            return []
        res = (def2loc(defs) if include_decl else []) + def2loc(refs)
        logging.info("textDocument/references return %s", res)
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
