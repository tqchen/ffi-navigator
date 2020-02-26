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

  py::class_<Object>(m, "ScriptObject")
      .def("_type", [](Module& m) { return m.type(); })
      .def(
          "_get_method",
          [](Object& self, const std::string& name) -> Method {
            return self.get_method(name);
          },
          py::keep_alive<0, 1>())
      .def(
          "setattr",
          [](Object& self, const std::string& name, py::object value) {
            if (self.type()->hasConstant(name)) {
              TORCH_CHECK(
                  false,
                  "Can't set constant '",
                  name,
                  "' which has value:",
                  self.type()->getConstant(name));
            }
            TypePtr type = self.type()->getAttribute(name);
            auto ivalue = toIValue(std::move(value), type);
            self.setattr(name, ivalue);
          })
      .def(
          "getattr",
          [](Object& self, const std::string& name) {
            return toPyObject(self.attr(name));
          })
      .def(
          "__getattr__",
          [](Object& self, const std::string& name) {
            if (auto method = self.find_method(name)) {
              return py::cast(*method);
            }
            return toPyObject(self.attr(name));
          })
      .def(
          "hasattr",
          [](Object& self, const std::string& name) {
            return self.hasattr(name);
          })
      .def(
          "_has_method",
          [](Object& self, const std::string& name) {
            return bool(self.find_method(name));
          })

  py::class_<Module, Object>(m, "ScriptModule")
      .def(py::init<std::string, std::shared_ptr<CompilationUnit>, bool>())
      .def(
          "save",
          [](Module& m,
             const std::string& filename,
             const ExtraFilesMap& _extra_files = ExtraFilesMap()) {
            m.save(filename, _extra_files);
          },
          py::arg("filename"),
          py::arg("_extra_files") = ExtraFilesMap())
      .def(
          "save_to_buffer",
          [](Module& m, const ExtraFilesMap& _extra_files = ExtraFilesMap()) {
            std::ostringstream buf;
            m.save(buf, _extra_files);
            return py::bytes(buf.str());
          },
          py::arg("_extra_files") = ExtraFilesMap())
      .def(
          "get_debug_state",
          [](Module& self) {
            if (auto m = self.find_method("forward")) {
              return m->get_executor().getDebugState();
            }
            throw std::runtime_error(
                "Attempted to call get_debug_state on a Module without a compiled forward()");
          })
      .def(
          "_define",
          [](Module& m,
             std::shared_ptr<ConcreteModuleType> concreteType,
             const std::string& script,
             ResolutionCallback rcb) {
            const auto self = ModuleSelf(std::move(concreteType));
            m._ivalue()->compilation_unit()->define(
                *m.type()->name(), script, pythonResolver(rcb), &self);
            didFinishEmitModule(m);
          })
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

}
