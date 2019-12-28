"""Language server using the navigator"""
import argparse
import logging
import pathlib
import attr
import os
import sys
from urllib.parse import urlparse
from . import workspace, pattern, lsp
from pyls_jsonrpc import endpoint, streams
from pyls import python_ls


def uri2path(uri):
    return urlparse(uri).path

def path2uri(path):
    return pathlib.Path(os.path.abspath(path)).as_uri()


class BaseServer(python_ls.PythonLanguageServer):
    """Base language server can be used for unittesting."""
    def __init__(self):
        super(BaseServer, self).__init__(sys.stdin.buffer, sys.stdout.buffer)
        self.endpoint = None
        self.logger = logging
        self.ws = workspace.Workspace()

    def m_initialize(self, **kwargs):
        self.logger.info("Initialize %s", kwargs)
        rooturi = kwargs["rootUri"]
        if rooturi is not None:
            root_path = uri2path(kwargs["rootUri"])
            self.ws.initialize(root_path)
        return super(BaseServer, self).m_initialize(**kwargs)

    def m_initialized(self, **kwargs):
        pass

    def m_text_document__definition(self, **kwargs):
        path = uri2path(kwargs["textDocument"]["uri"])
        logging.info("textDocument/definition %s", kwargs)
        pos = lsp.Position(**kwargs["position"])
        expr = pattern.extract_expr(open(path).readlines(), pos)
        if expr is None:
            logging.error("textDocument/definition get None expression %s", kwargs)
            return []
        asloc = lambda decl: attr.asdict(lsp.Location(uri=path2uri(decl.path), range=decl.range))
        res = [asloc(x) for x in self.ws.get_definition(path, expr)]
        if res == []:
            res = super(BaseServer, self).m_text_document__definition(**kwargs)
        logging.info("textDocument/definition return %s", res)
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
