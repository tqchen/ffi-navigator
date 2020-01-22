void initJitScriptBindings(PyObject* module) {
  py::class_<CompilationUnit, std::shared_ptr<CompilationUnit>>(
      m, "CompilationUnit")
      .def(py::init<>())
      .def(
          "find_function",
          [](std::shared_ptr<CompilationUnit> self, const std::string& name) {
            auto& fn = self->get_function(QualifiedName(name));
            return StrongFunctionPtr(std::move(self), &fn);
          })
      .def("set_optimized", &CompilationUnit::set_optimized)
      .def(
          "define",
          [](CompilationUnit& cu,
             const std::string& src,
             ResolutionCallback rcb) {
            cu.define(c10::nullopt, src, pythonResolver(rcb), nullptr);
          });

  py::class_<StrongFunctionPtr>(m, "ScriptFunction", py::dynamic_attr())
      .def(
          "__call__",
          [](py::args args, py::kwargs kwargs) {
            HANDLE_TH_ERRORS
            // see: [pybind11 varargs]
            auto strongPtr = py::cast<StrongFunctionPtr>(args[0]);
            Function& callee = *strongPtr.function_;
            bool tracing = tracer::isTracing();
            py::object result = invokeScriptFunctionFromPython(
                callee, tuple_slice(std::move(args), 1), std::move(kwargs));
            return result;
            END_HANDLE_TH_ERRORS_PYBIND
          })
      .def(
          "save",
          [](const StrongFunctionPtr& self,
             const std::string& filename,
             const ExtraFilesMap& _extra_files = ExtraFilesMap()) {
            Module module("__torch__.PlaceholderModule");
            // [issue 27343]
            // Modules have 'training' attributes by defualt, but due to
            // https://github.com/pytorch/pytorch/issues/27343, functions end
            // up having a training attribute when they are loaded. This adds
            // a fake 'training' attribute that shouldn't be used, but prevents
            // jitter on saving and loading. Once that issue is fixed this can
            // be deleted.
            module.register_attribute("training", BoolType::get(), true);
            addFunctionToModule(module, self);
            module.save(filename, _extra_files);
          },
          py::arg("filename"),
          py::arg("_extra_files") = ExtraFilesMap())
      .def(
          "save_to_buffer",
          [](const StrongFunctionPtr& self,
             const ExtraFilesMap& _extra_files = ExtraFilesMap()) {
            std::ostringstream buf;
            Module module("__torch__.PlaceholderModule");
            // see [issue 27343]
            module.register_attribute("training", BoolType::get(), true);
            addFunctionToModule(module, self);
            module.save(buf, _extra_files);
            return py::bytes(buf.str());
          },
          py::arg("_extra_files") = ExtraFilesMap())
      .def_property_readonly(
          "graph",
          [](const StrongFunctionPtr& self) { return self.function_->graph(); })
      .def_property_readonly(
          "schema",
          [](const StrongFunctionPtr& self) {
            return self.function_->getSchema();
          })
      .def_property_readonly(
          "code",
          [](const StrongFunctionPtr& self) {
            std::vector<at::Tensor> tensors;
            std::vector<c10::NamedTypePtr> deps;
            PythonPrint pp(tensors, deps, false);
            pp.printFunction(*self.function_);
            return pp.str();
          })
      .def(
          "get_debug_state",
          [](const StrongFunctionPtr& self) {
            return self.function_->get_executor().getDebugState();
          })
      .def_property_readonly(
          "name",
          [](const StrongFunctionPtr& self) { return self.function_->name(); })
      .def_property_readonly(
          "qualified_name", [](const StrongFunctionPtr& self) {
            return self.function_->qualname().qualifiedName();
          });

  m.def("_jit_script_class_compile", [](const std::string &qualifiedName,
                                        const ClassDef &classDef,
                                        ResolutionCallback rcb) {
    C10_LOG_API_USAGE_ONCE("torch.script.class");
    if (classDef.superclass().present()) {
      throw ErrorReport(classDef.range())
          << "Torchscript does not support class inheritance.";
    }
    auto cu = get_python_cu();
    const auto classname = c10::QualifiedName(qualifiedName);
    auto classType = ClassType::create(classname, cu);
    cu->register_type(classType);
    std::vector<ResolverPtr> rcbs;
    std::vector<Def> methodDefs;
    for (const auto &def : classDef.body()) {
      if (def.kind() != TK_DEF) {
        throw ErrorReport(def.range())
            << "Currently class bodies can only contain method "
               "definitions. File an issue on Github if you want "
               "something else!";
      }
      methodDefs.emplace_back(Def(def));
      rcbs.push_back(pythonResolver(rcb, classDef.name().name(), classType));
    }
    const auto self = SimpleSelf(classType);
    cu->define(classname, methodDefs, rcbs, &self);
  });

  py::class_<Module, Object>(m, "ScriptModule")
      .def(py::init<std::string, std::shared_ptr<CompilationUnit>, bool>())
      .def(
          "_create_method_from_trace",
          [](Module& self,
             const std::string& name,
             py::function func,
             py::tuple input_tuple,
             py::function var_lookup_fn,
             bool force_outplace) {
            // prereq: Module's buffers and parameters are unique
            // this was ensured in python before calling this function
            auto typed_inputs = toTraceableStack(input_tuple);

            std::shared_ptr<Graph> graph = std::get<0>(tracer::createGraphByTracing(
                func, typed_inputs, var_lookup_fn, force_outplace, &self));
            const auto method_name = QualifiedName(*self.type()->name(), name);
            auto fn = self._ivalue()->compilation_unit()->create_function(
                method_name, graph);
            self.type()->addMethod(fn);
            didFinishEmitModule(self);
          });
}
