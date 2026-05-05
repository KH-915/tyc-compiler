"""
Code generator for TyC.
"""

from typing import Any

from ..utils.nodes import *
from ..utils.visitor import BaseVisitor
from .emitter import *
from .frame import *
from .io import IO_SYMBOL_LIST
from .utils import *
from .error import *


class StringArrayType:
    """Marker type for JVM main(String[] args)."""
    pass


class CodeGenerator(BaseVisitor):
    """Minimal AST -> Jasmin code generator."""

    def __init__(self):
        self.emit = None
        self.functions = {}
        self.current_return_type = VoidType()
        self.class_name = "TyC"

    def _lookup_symbol(self, name: str, sym_list: list[Symbol]) -> Symbol:
        for sym in reversed(sym_list):
            if sym.name == name:
                return sym
        raise RuntimeError(f"Undeclared symbol: {name}")

    def _infer_type(self, node: Expr, o: Access):
        if isinstance(node, IntLiteral):
            return IntType()
        if isinstance(node, FloatLiteral):
            return FloatType()
        if isinstance(node, StringLiteral):
            return StringType()
        if isinstance(node, Identifier):
            return self._lookup_symbol(node.name, o.sym).type
        if isinstance(node, AssignExpr):
            return self._infer_type(node.rhs, o)
        if isinstance(node, FuncCall):
            return self.functions[node.name].type.return_type
        if isinstance(node, BinaryOp):
            if node.operator in ["+", "-", "*", "/", "%"]:
                left_type = self._infer_type(node.left, o)
                right_type = self._infer_type(node.right, o)
                if is_float_type(left_type) or is_float_type(right_type):
                    return FloatType()
                return IntType()
            if node.operator in ["<", "<=", ">", ">=", "==", "!="]:
                return IntType()
        return IntType()

    def visit_program(self, node: Program, o: Any = None):
        print("Starting code generation for Program")  # Debugging statement
        self.emit = Emitter(f"{self.class_name}.j")
        self.emit.print_out(self.emit.emit_prolog(self.class_name))

        for io_sym in IO_SYMBOL_LIST:
            self.functions[io_sym.name] = io_sym

        for decl in node.decls:
            if isinstance(decl, FuncDecl):
                return_type = decl.return_type if decl.return_type else VoidType()
                param_types = [p.param_type for p in decl.params]
                self.functions[decl.name] = Symbol(
                    decl.name, FunctionType(param_types, return_type), CName(self.class_name)
                )

        for decl in node.decls:
            if isinstance(decl, FuncDecl):
                self.visit(decl, None)

        self.emit.emit_epilog()
        print("Finished code generation for Program")  # Debugging statement

    def visit_func_decl(self, node: FuncDecl, o: Any = None):
        print(f"Visiting FuncDecl: {node.name}")  # Debugging statement
        self.current_return_type = node.return_type if node.return_type else VoidType()
        frame = Frame(node.name, self.current_return_type)
        frame.enter_scope(True)

        if node.name == "main":
            mtype = FunctionType([StringArrayType()], VoidType())
        else:
            mtype = FunctionType([p.param_type for p in node.params], self.current_return_type)

        self.emit.print_out(self.emit.emit_method(node.name, mtype, True))

        start_label = frame.get_start_label()
        end_label = frame.get_end_label()
        self.emit.print_out(self.emit.emit_label(start_label, frame))

        local_syms: list[Symbol] = []
        if node.name == "main":
            args_idx = frame.get_new_index()
            self.emit.print_out(
                self.emit.emit_var(
                    args_idx, "args", StringArrayType(), start_label, end_label
                )
            )

        for param in node.params:
            idx = frame.get_new_index()
            self.emit.print_out(
                self.emit.emit_var(idx, param.name, param.param_type, start_label, end_label)
            )
            local_syms.append(Symbol(param.name, param.param_type, Index(idx)))

        sub_body = SubBody(frame, local_syms)
        self.visit(node.body, sub_body)

        if is_void_type(self.current_return_type):
            self.emit.print_out(self.emit.emit_return(VoidType(), frame))

        self.emit.print_out(self.emit.emit_label(end_label, frame))
        
        # FIX: Add a dummy return to satisfy the JVM Verifier for non-void functions
        if not is_void_type(self.current_return_type):
            if type(self.current_return_type) is FloatType:
                self.emit.print_out(self.emit.emit_push_fconst("0.0", frame))
            elif type(self.current_return_type) is IntType:
                self.emit.print_out(self.emit.emit_push_iconst(0, frame))
            else:
                frame.push()
                self.emit.print_out(self.emit.jvm.emitPUSHNULL())
            self.emit.print_out(self.emit.emit_return(self.current_return_type, frame))

        frame.exit_scope()
        self.emit.print_out(self.emit.emit_end_method(frame))
        print(f"Finished visiting FuncDecl: {node.name}")  # Debugging statement

    def visit_block_stmt(self, node: BlockStmt, o: SubBody = None):
        if o is None:
            raise RuntimeError("Environment 'o' was lost before reaching BlockStmt.")
        o.frame.enter_scope(False)
        
        # FIX: Print the starting label for the variables in this block
        self.emit.print_out(self.emit.emit_label(o.frame.get_start_label(), o.frame))
        
        env = o.sym.copy() 
        sub_o = SubBody(o.frame, env)
        
        for stmt in node.statements:
            self.visit(stmt, sub_o)
            
        # FIX: Print the ending label for the variables in this block
        self.emit.print_out(self.emit.emit_label(o.frame.get_end_label(), o.frame))
        
        o.frame.exit_scope()
        return o

    def visit_var_decl(self, node: VarDecl, o: SubBody = None):
        if o is None:
            raise RuntimeError("Environment 'o' was lost before reaching VarDecl.")
        frame = o.frame
        idx = frame.get_new_index()
        var_type = node.var_type if node.var_type else self._infer_type(node.init_value, Access(frame, o.sym))
        self.emit.print_out(
            self.emit.emit_var(
                idx, node.name, var_type, frame.get_start_label(), frame.get_end_label()
            )
        )
        if node.init_value is not None:
            rhs_code, _ = self.visit(node.init_value, Access(frame, o.sym))
            self.emit.print_out(rhs_code)
            self.emit.print_out(self.emit.emit_write_var(node.name, var_type, idx, frame))
        o.sym.append(Symbol(node.name, var_type, Index(idx)))
        return o

    def visit_expr_stmt(self, node: ExprStmt, o: SubBody = None):
        code, expr_type = self.visit(node.expr, Access(o.frame, o.sym))
        self.emit.print_out(code)
        if not is_void_type(expr_type):
            self.emit.print_out(self.emit.emit_pop(o.frame))
        return o

    def visit_if_stmt(self, node: IfStmt, o: SubBody = None):
        frame = o.frame
        cond_code, _ = self.visit(node.condition, Access(frame, o.sym))
        else_label = frame.get_new_label()
        end_label = frame.get_new_label()
        self.emit.print_out(cond_code)
        self.emit.print_out(self.emit.emit_if_false(else_label, frame))
        self.visit(node.then_stmt, o)
        self.emit.print_out(self.emit.emit_goto(end_label, frame))
        self.emit.print_out(self.emit.emit_label(else_label, frame))
        if node.else_stmt:
            self.visit(node.else_stmt, o)
        self.emit.print_out(self.emit.emit_label(end_label, frame))
        return o

    def visit_while_stmt(self, node: WhileStmt, o: SubBody = None):
        frame = o.frame
        
        # MISSING LOOP HOOKS
        frame.enter_loop() 
        
        start_label = frame.get_new_label()
        end_label = frame.get_break_label()
        con_label = frame.get_continue_label() # While loops continue at the condition
        
        self.emit.print_out(self.emit.emit_label(start_label, frame))
        self.emit.print_out(self.emit.emit_label(con_label, frame))
        
        cond_code, _ = self.visit(node.condition, Access(frame, o.sym))
        self.emit.print_out(cond_code)
        self.emit.print_out(self.emit.emit_if_false(end_label, frame))
        
        self.visit(node.body, o)
        
        self.emit.print_out(self.emit.emit_goto(start_label, frame))
        self.emit.print_out(self.emit.emit_label(end_label, frame))
        
        frame.exit_loop()
        return o

    def visit_return_stmt(self, node: ReturnStmt, o: SubBody = None):
        if node.expr is None:
            self.emit.print_out(self.emit.emit_return(VoidType(), o.frame))
            return o
        code, ret_type = self.visit(node.expr, Access(o.frame, o.sym))
        self.emit.print_out(code)
        self.emit.print_out(self.emit.emit_return(ret_type, o.frame))
        return o

    def visit_binary_op(self, node: BinaryOp, o: Access = None):
        left_code, left_type = self.visit(node.left, o)
        right_code, right_type = self.visit(node.right, o)
        frame = o.frame
        
        # --- MISSING LOGICAL OPERATORS FIX ---
        if node.operator in ["&&", "and"]:
            return left_code + right_code + self.emit.emit_and_op(frame), IntType()
        if node.operator in ["||", "or"]:
            return left_code + right_code + self.emit.emit_or_op(frame), IntType()
            
        # --- IMPLICIT CASTING FIX ---
        is_f1 = is_float_type(left_type)
        is_f2 = is_float_type(right_type)
        result_type = FloatType() if is_f1 or is_f2 else IntType()

        # Inject i2f if one is float and the other is int
        if is_f1 and not is_f2:
            right_code += self.emit.emit_i2f(frame)
        elif is_f2 and not is_f1:
            left_code += self.emit.emit_i2f(frame)

        # Original operator logic continues...
        if node.operator in ["+", "-"]:
            return left_code + right_code + self.emit.emit_add_op(node.operator, result_type, frame), result_type
        if node.operator in ["*", "/"]:
            return left_code + right_code + self.emit.emit_mul_op(node.operator, result_type, frame), result_type
        if node.operator == "%":
            return left_code + right_code + self.emit.emit_mod(frame), IntType()
        if node.operator in ["<", "<=", ">", ">=", "==", "!="]:
            return left_code + right_code + self.emit.emit_re_op(node.operator, result_type, frame), IntType()
            
        raise RuntimeError(f"Unsupported operator: {node.operator}")

    def visit_assign_expr(self, node: AssignExpr, o: Access = None):
        rhs_code, rhs_type = self.visit(node.rhs, o)
        
        # 1. Identifier Assignment
        if isinstance(node.lhs, Identifier):
            lhs_sym = self._lookup_symbol(node.lhs.name, o.sym)
            idx = lhs_sym.value.value
            code = rhs_code + self.emit.emit_dup(o.frame) + self.emit.emit_write_var(
                node.lhs.name, lhs_sym.type, idx, o.frame
            )
            return code, rhs_type
            
        # 2. Struct Member Assignment (obj.field = value)
        elif isinstance(node.lhs, MemberAccess):
            obj_code, obj_type = self.visit(node.lhs.obj, o)
            member_type = self._infer_type(node.lhs, o)
            lexeme = f"{obj_type.struct_name}/{node.lhs.member}"
            
            # Stack before PutField needs to be: [..., objectref, value]
            # DUP_X1 duplicates the value and puts it under the objectref
            code = obj_code + rhs_code + self.emit.emit_dup_x1(o.frame) + self.emit.emit_put_field(lexeme, member_type, o.frame)
            return code, rhs_type
            
        # 3. Array Index Assignment (arr[idx] = value)
        elif type(node.lhs).__name__ == "ArrayAccess": # Check class name safely
            arr_code, arr_type = self.visit(node.lhs.arr, o)
            idx_code, _ = self.visit(node.lhs.idx, o)
            
            # Stack before ArrayStore: [..., arrayref, index, value]
            # DUP_X2 duplicates the value and puts it under both arrayref and index
            code = arr_code + idx_code + rhs_code + self.emit.emit_dup_x2(o.frame)
            
            if is_int_type(rhs_type):
                code += self.emit.jvm.emitIASTORE()
            elif is_float_type(rhs_type):
                code += self.emit.jvm.emitFASTORE()
            else:
                code += self.emit.jvm.emitAASTORE()
                
            return code, rhs_type
            
        raise RuntimeError("Unsupported assignment left-hand side")

    def visit_func_call(self, node: FuncCall, o: Access = None):
        frame = o.frame
        fn_sym = self.functions[node.name]
        fn_type = fn_sym.type
        code = ""
        for arg in node.args:
            arg_code, _ = self.visit(arg, o)
            code += arg_code
        code += self.emit.emit_invoke_static(f"{fn_sym.value.value}/{node.name}", fn_type, frame)
        return code, fn_type.return_type

    def visit_identifier(self, node: Identifier, o: Access = None):
        sym = self._lookup_symbol(node.name, o.sym)
        return self.emit.emit_read_var(node.name, sym.type, sym.value.value, o.frame), sym.type

    def visit_int_literal(self, node: IntLiteral, o: Access = None):
        return self.emit.emit_push_iconst(node.value, o.frame), IntType()

    def visit_float_literal(self, node: FloatLiteral, o: Access = None):
        return self.emit.emit_push_fconst(str(node.value), o.frame), FloatType()

    def visit_string_literal(self, node: StringLiteral, o: Access = None):
        return self.emit.emit_push_const(node.value, StringType(), o.frame), StringType()

    def visit_struct_decl(self, node: StructDecl, o: Any = None):
        return None

    def visit_member_decl(self, node: MemberDecl, o: Any = None):
        return None

    def visit_param(self, node: Param, o: Any = None):
        return None

    def visit_int_type(self, node: IntType, o: Any = None):
        return node

    def visit_float_type(self, node: FloatType, o: Any = None):
        return node

    def visit_string_type(self, node: StringType, o: Any = None):
        return node

    def visit_void_type(self, node: VoidType, o: Any = None):
        return node

    def visit_struct_type(self, node: StructType, o: Any = None):
        return node

    def visit_case_stmt(self, node: CaseStmt, o: SubBody = None):
        if o is None:
            raise RuntimeError("Environment 'o' was lost before reaching CaseStmt.")
            
        # Extract statements and ensure it's an iterable list
        stmts = node.statements if hasattr(node, 'statements') else getattr(node, 'body', [])
        if not isinstance(stmts, list): 
            stmts = [stmts]
            
        # Visit inner statements
        for stmt in stmts:
            self.visit(stmt, o)
            
        return o


    def visit_default_stmt(self, node: DefaultStmt, o: SubBody = None):
        if o is None:
            raise RuntimeError("Environment 'o' was lost before reaching DefaultStmt.")

        # Extract statements and ensure it's an iterable list
        def_stmts = node.statements if hasattr(node, 'statements') else getattr(node, 'body', [])
        if not isinstance(def_stmts, list): 
            def_stmts = [def_stmts]
        
        # Visit inner statements
        for s in def_stmts:
            self.visit(s, o)
            
        return o


    def visit_switch_stmt(self, node: SwitchStmt, o: SubBody = None):
        if o is None:
            raise RuntimeError("Environment 'o' was lost before reaching SwitchStmt.")
            
        current_frame = o.frame
        current_frame.enter_loop() # Switch acts as a breakable context
        brk_label = current_frame.get_break_label()
        env_access = Access(current_frame, o.sym)
        
        # 1. Evaluate switch expression
        expr_code, expr_type = self.visit(node.expr, env_access)
        self.emit.print_out(expr_code)
        
        # 2. Store in a temporary variable (explicitly declared to satisfy JVM Verifier)
        temp_idx = current_frame.get_new_index()
        self.emit.print_out(self.emit.emit_var(temp_idx, "switch_tmp", expr_type, current_frame.get_start_label(), current_frame.get_end_label()))
        self.emit.print_out(self.emit.emit_write_var("switch_tmp", expr_type, temp_idx, current_frame))
        
        # 3. Pre-generate labels for the Jump Table routing
        case_labels = [current_frame.get_new_label() for _ in node.cases]
        default_label = current_frame.get_new_label()
        
        # 4. Emit the Condition Jump Table (Routing logic)
        for i, case in enumerate(node.cases):
            self.emit.print_out(self.emit.emit_read_var("switch_tmp", expr_type, temp_idx, current_frame))
            
            c_val = case.value if hasattr(case, 'value') else case.expr
            v_code, _ = self.visit(c_val, env_access)
            self.emit.print_out(v_code)
            
            # Pop both values from the simulated stack to keep JVM stack mathematically balanced
            current_frame.pop()
            current_frame.pop()
            
            # Direct JVM routing checks
            if type(expr_type) is IntType:
                self.emit.print_out(self.emit.jvm.emitIFICMPEQ(case_labels[i]))
            elif type(expr_type) is FloatType:
                self.emit.print_out(self.emit.jvm.emitFCMPL())
                self.emit.print_out(self.emit.jvm.emitIFEQ(case_labels[i]))
            else:
                self.emit.print_out(self.emit.jvm.emitIFACMPEQ(case_labels[i]))
                
        # If nothing matched in the jump table, jump to default
        self.emit.print_out(self.emit.emit_goto(default_label, current_frame))
        
        # 5. Delegate to Case Visitors (Separated Logic)
        for i, case in enumerate(node.cases):
            self.emit.print_out(self.emit.emit_label(case_labels[i], current_frame))
            # Delegation happens here:
            self.visit(case, o) 
                
        # 6. Delegate to Default Visitor (Separated Logic)
        self.emit.print_out(self.emit.emit_label(default_label, current_frame))
        def_node = getattr(node, 'default_stmt', getattr(node, 'default_case', None))
        
        if def_node:
            # Delegation happens here:
            self.visit(def_node, o) 
                
        # 7. End of Switch Block
        self.emit.print_out(self.emit.emit_label(brk_label, current_frame))
        current_frame.exit_loop()
        
        return o
    
    def visit_break_stmt(self, node: BreakStmt, o: SubBody = None):
        print("Visiting BreakStmt")  # Debugging statement
        # Jump to the current loop's break label
        brk_label = o.frame.get_break_label()
        if(brk_label is None):
            raise IllegalRuntimeException("Break statement outside of a loop or switch context")
        self.emit.print_out(self.emit.emit_goto(brk_label, o.frame))
        print("Visited BreakStmt")
        return o

    def visit_continue_stmt(self, node: ContinueStmt, o: SubBody = None):
        # Jump to the current loop's continue label
        self.emit.print_out(self.emit.emit_goto(o.frame.get_continue_label(), o.frame))
        print("Visited ContinueStmt")
        return o

    def visit_for_stmt(self, node: ForStmt, o: SubBody = None):
        frame = o.frame
        
        # 1. Evaluate Initialization and POP the leftover value
        if node.init:
            if(isinstance(node.init, VarDecl)):
                self.visit(node.init, o) # VarDecl handles its own codegen and symbol table insertion
            else:
                init_code, init_type = self.visit(node.init, o)
                self.emit.print_out(init_code)
                # Prevent stack pollution from Assignment dup
                self.emit.print_out(self.emit.emit_pop(frame))

        frame.enter_loop()
        start_label = frame.get_new_label()
        con_label = frame.get_continue_label()
        brk_label = frame.get_break_label()
        
        self.emit.print_out(self.emit.emit_label(start_label, frame))
        
        if node.condition:
            cond_code, _ = self.visit(node.condition, Access(frame, o.sym))
            self.emit.print_out(cond_code)
            self.emit.print_out(self.emit.emit_if_false(brk_label, frame))
            
        self.visit(node.body, o)
        self.emit.print_out(self.emit.emit_label(con_label, frame))
        
        # Evaluate Update and POP the leftover value
        if node.update:
            update_code, update_type = self.visit(node.update, o)
            self.emit.print_out(update_code)
            self.emit.print_out(self.emit.emit_pop(frame))
            
        self.emit.print_out(self.emit.emit_goto(start_label, frame))
        self.emit.print_out(self.emit.emit_label(brk_label, frame))
        
        frame.exit_loop()
        return o
    
    def visit_prefix_op(self, node: PrefixOp, o: Access = None):
        code, typ = self.visit(node.operand, o)
        if node.operator == '-':
            return code + self.emit.emit_neg_op(typ, o.frame), typ
        elif node.operator == '!':
            # Logical NOT: Compare with 0. If 0 -> 1, If non-zero -> 0
            label_false = o.frame.get_new_label()
            label_end = o.frame.get_new_label()
            res = code
            res += self.emit.emit_if_true(label_false, o.frame)
            res += self.emit.emit_push_iconst(1, o.frame)
            res += self.emit.emit_goto(label_end, o.frame)
            res += self.emit.emit_label(label_false, o.frame)
            res += self.emit.emit_push_iconst(0, o.frame)
            res += self.emit.emit_label(label_end, o.frame)
            return res, IntType()

    def visit_postfix_op(self, node: PostfixOp, o: SubBody = None):
        # Postfix ++ / -- (Assumes it only applies to identifiers)
        sym = self._lookup_symbol(node.operand.name, o.sym)
        idx = sym.value.value
        frame = o.frame
        
        # Read current value onto stack (this is the returned value)
        code = self.emit.emit_read_var(sym.name, sym.type, idx, frame)
        
        # Do the math and store it back
        code += self.emit.emit_read_var(sym.name, sym.type, idx, frame)
        code += self.emit.emit_push_iconst(1, frame)
        code += self.emit.emit_add_op('+' if node.operator == '++' else '-', sym.type, frame)
        code += self.emit.emit_write_var(sym.name, sym.type, idx, frame)
        
        return code, sym.type

    def visit_member_access(self, node: MemberAccess, o: Access = None):
        obj_code, obj_type = self.visit(node.obj, o)
        
        # You need a helper to look up the field's type based on struct_name
        # Assuming you have an environment mapping structs to their fields:
        member_type = self._infer_type(node, o) 
        
        lexeme = f"{obj_type.struct_name}/{node.member}"
        code = obj_code + self.emit.emit_get_field(lexeme, member_type, o.frame)
        return code, member_type

    def visit_array_access(self, node, o: Access = None): # Assuming node type is ArrayAccess
        arr_code, arr_type = self.visit(node.arr, o)
        idx_code, _ = self.visit(node.idx, o)
        
        code = arr_code + idx_code
        
        # Emitter assumes iaload, faload, aaload based on element type
        if is_int_type(arr_type.element_type):
            code += self.emit.jvm.emitIALOAD()
        elif is_float_type(arr_type.element_type):
            code += self.emit.jvm.emitFALOAD()
        else:
            code += self.emit.jvm.emitAALOAD()
            
        return code, arr_type.element_type
    
    def visit_struct_literal(self, node: StructLiteral, o: Any = None):
        """
        Visits the arguments of a struct literal.
        Note: Because a raw `{...}` literal lacks the struct name in the AST, 
        full JVM object instantiation is typically handled inside `visit_var_decl` 
        or `visit_assign_expr` where the target type is known.
        """
        code = ""
        # Evaluate all arguments inside the struct literal and push them to the stack
        for arg in node.args:
            arg_code, _ = self.visit(arg, o)
            code += arg_code
            
        # Return the generated code and a generic/placeholder type
        return code, StructType("Unknown")

