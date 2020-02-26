class Variable : public ExprNode {
 public:
  /*!
   * \brief The hint to the variable name.
   * \note Each variable is uniquely identified by its address.
   */
  std::string name_hint;

  static Var make(DataType dtype, std::string name_hint);

  void VisitAttrs(AttrVisitor* v) {
    v->Visit("dtype", &dtype);
    v->Visit("name", &name_hint);
  }

  static constexpr const char* _type_key = "Variable";
  TVM_DECLARE_FINAL_OBJECT_INFO(Variable, ExprNode);
};
