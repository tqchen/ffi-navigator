#include <mxnet/base.h>
#include <mxnet/c_api.h>
#include <mxnet/executor.h>
#include <mxnet/imperative.h>
#include "./c_api_common.h"
#include "../executor/graph_executor.h"
#include "../common/utils.h"

int MXExecutorPrint(ExecutorHandle handle, const char **out_str) {
  Executor *exec = static_cast<Executor*>(handle);
  MXAPIThreadLocalEntry<> *ret = MXAPIThreadLocalStore<>::Get();
  API_BEGIN();
  std::ostringstream os;
  exec->Print(os);
  ret->ret_str = os.str();
  *out_str = (ret->ret_str).c_str();
  API_END();
}

int MXExecutorFree(ExecutorHandle handle) {
  API_BEGIN();
  delete static_cast<Executor*>(handle);
  API_END();
}

int MXExecutorForward(ExecutorHandle handle, int is_train) {
  API_BEGIN();
  Executor *exec = static_cast<Executor*>(handle);
  exec->Forward(is_train != 0);
  API_END();
}
