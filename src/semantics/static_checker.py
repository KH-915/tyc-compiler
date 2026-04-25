"""
Static Semantic Checker for TyC Programming Language

This module implements a comprehensive static semantic checker using visitor pattern
for the TyC procedural programming language. It performs type checking,
scope management, type inference, and detects all semantic errors as
specified in the TyC language specification.
"""

from functools import reduce
from typing import (
    Dict,
    List,
    Set,
    Optional,
    Any,
    Tuple,
    NamedTuple,
    Union,
    TYPE_CHECKING,
)
from unicodedata import name
from ..utils.visitor import ASTVisitor
from ..utils.nodes import (
    ASTNode,
    Program,
    StructDecl,
    MemberDecl,
    FuncDecl,
    Param,
    VarDecl,
    IfStmt,
    WhileStmt,
    ForStmt,
    BreakStmt,
    ContinueStmt,
    ReturnStmt,
    BlockStmt,
    SwitchStmt,
    CaseStmt,
    DefaultStmt,
    Type,
    IntType,
    FloatType,
    StringType,
    VoidType,
    StructType,
    BinaryOp,
    PrefixOp,
    PostfixOp,
    AssignExpr,
    MemberAccess,
    FuncCall,
    Identifier,
    StructLiteral,
    IntLiteral,
    FloatLiteral,
    StringLiteral,
    ExprStmt,
    Expr,
    Stmt,
    Decl,
)

# Type aliases for better type hints
TyCType = Union[IntType, FloatType, StringType, VoidType, StructType]
from static_error import (
    StaticError,
    Redeclared,
    UndeclaredIdentifier,
    UndeclaredFunction,
    UndeclaredStruct,
    TypeCannotBeInferred,
    TypeMismatchInStatement,
    TypeMismatchInExpression,
    MustInLoop,
)

# 1. Redeclared - Variables, functions, structs, or parameters declared multiple times
# 2. UndeclaredIdentifier - Use of variables or parameters that have not been declared
# 3. UndeclaredFunction - Use of functions that have not been declared
# 4. UndeclaredStruct - Use of struct types that have not been declared
# 5. TypeCannotBeInferred - Variables declared with `auto` whose type cannot be determined
# 6. TypeMismatchInStatement - Type incompatibilities in statements (if, while, for, return, assignment)
# 7. TypeMismatchInExpression - Type incompatibilities in expressions (operators, function calls, member access)
# 8. MustInLoop - Break/continue statements outside of loop contexts

class AssignStmt(Stmt):
    """Assignment statement (e.g., a = 5;).
    This is used when the assignment is a standalone statement.
    For assignments used in expressions (e.g., (a = 5) + 7), use AssignExpr.
    """

    def __init__(self, stmt: "AssignExpr"):
        super().__init__()
        self.stmt = stmt

    def accept(self, visitor, o=None):
        return visitor.visit_assign_stmt(self, o)

    def __str__(self):
        return f"AssignStmt({self.stmt})"
class StaticChecker(ASTVisitor):
    def check_program(self, ast: Any) -> str:
        #print("Starting static semantic check...")
        #print(ast)
        self.visit_program(ast)
        #print("Static semantic check completed successfully.")
        
    
    def visit_program(self, node: "Program", o: Any = None):
        #print("Started visiting Program node...")
        o = {
            "scopes": [ {} ],        # stack of variable scopes
            "functions": {
                "readInt": FuncDecl(name="readInt", return_type=IntType(), params=[], body=None),
                "readFloat": FuncDecl(name="readFloat", return_type=FloatType(), params=[], body=None),
                "readString": FuncDecl(name="readString", return_type=StringType(), params=[], body=None),
                "#printInt": FuncDecl(name="#printInt", return_type=VoidType(), params=[IntType()], body=None),
                "#printFloat": FuncDecl(name="#printFloat", return_type=VoidType(), params=[FloatType()], body=None),
                "#printString": FuncDecl(name="#printString", return_type=VoidType(), params=[StringType()], body=None)
            },         # name -> FuncDecl
            "structs": {},           # name -> StructDecl
            "current_return": None,
            "in_loop": 0,
            "in_switch": 0,
            "is_in_func": 0
        }
        for decl in node.decls:
            self.visit(decl, o)
        #print("Finished visiting Program node.")

    def visit_struct_decl(self, node: "StructDecl", o: Any = None):
        #print(f"Started visiting StructDecl node: {node.name}")
        if node.name in o["structs"]:
            raise Redeclared("Struct", node.name)

        field_names = {}
        self.enter_scope(o) # Enter a new scope for struct members to allow nested struct definitions
        for mem in node.members:
            if mem.name in field_names:
                raise Redeclared("Member", mem.name)
            field_names[mem.name] = mem.member_type
            self.visit(mem, o)

        self.exit_scope(o)

        o["structs"][node.name] = field_names
        self.declare(node.name, StructType(node.name), o) # Declare struct name in the current scope
        #print(f"Finished visiting StructDecl node: {node.name}")

    def visit_member_decl(self, node: "MemberDecl", o: Any = None):
        #print(f"Started visiting MemberDecl node: {node.name}")
        if node.name in o["scopes"][-1]:
            raise Redeclared("Variable", node.name)
        self.declare(node.name, node.member_type, o)
        #print(f"Finished visiting MemberDecl node: {node.name}")

    def visit_func_decl(self, node: "FuncDecl", o: Any = None):
        #print(f"Started visiting FuncDecl node: {node.name}")
        #print(self.lookup(node.name, o))
        if node.name in o["functions"] or self.lookup(node.name, o) != "Undeclared" or node.name in o["structs"]:
            raise Redeclared("Function", node.name)

        o["functions"][node.name] = node
        self.declare(node.name, node.return_type, o) # Declare function name in the current scope for potential recursive calls
        self.enter_scope(o)
        o["current_return"] = node.return_type
        for param in node.params:
            if param.name in o["scopes"][-1]:
                raise Redeclared("Parameter", param.name)
            #print(f"Declaring parameter: {param.name} of type {param.param_type}")
            self.declare(param.name, param.param_type, o)

        o["is_in_func"] += 1
        #print(f"Visiting function body of '{node.name}' with return type {node.return_type}")
        self.visit(node.body, o)
        o["is_in_func"] -= 1
        self.exit_scope(o)
        #print(f"Finished visiting FuncDecl node: {node.name}")

    # Type system
    def visit_int_type(self, node: "IntType", o: Any = None):
        #print ("Visiting IntType node")
        return IntType()

    def visit_float_type(self, node: "FloatType", o: Any = None):
        #print("Visiting FloatType node")
        return FloatType()

    def visit_string_type(self, node: "StringType", o: Any = None):
        #print("Visiting StringType node")
        return StringType()

    def visit_void_type(self, node: "VoidType", o: Any = None):
        #print("Visiting VoidType node")
        return VoidType()

    def visit_struct_type(self, node: "StructType", o: Any = None):
        #print(f"Started visiting StructType node: {node.struct_name}")
        if node.struct_name not in o["structs"]:
            raise UndeclaredStruct(node.struct_name)
        #print(f"Finished visiting StructType node: {node.struct_name}")
        return StructType(node.struct_name)

    # Statements
    def visit_block_stmt(self, node, o):
        # Use a local flag to remember if this block belongs directly to a function
        is_func_body = False
        
        if o["is_in_func"] > 0:
            #print("Started visiting BlockStmt node (function body)")
            is_func_body = True
            o["is_in_func"] -= 1
        else:
            #print("Started visiting BlockStmt node")
            self.enter_scope(o)

        i = 0
        statements = node.statements
        while i < len(statements):
            stmt = statements[i]
            
            # Workaround for parser bug: standalone function calls parsed as AssignStmt(Identifier) + ExprStmt(args)
            if isinstance(stmt, AssignStmt) and isinstance(stmt.stmt, Identifier):
                func_name = stmt.stmt.name
                
                # Verify this identifier represents a function (or an undeclared one)
                if func_name in o["functions"] or self.lookup(func_name, o) == "Undeclared":
                    if func_name not in o["functions"]:
                        raise UndeclaredFunction(func_name)
                        
                    func_decl = o["functions"][func_name]
                    num_args = len(func_decl.params)
                    
                    # Gather the expected number of arguments from the sequential ExprStmts
                    args = []
                    for j in range(num_args):
                        if i + 1 + j < len(statements) and isinstance(statements[i + 1 + j], ExprStmt):
                            args.append(statements[i + 1 + j].expr)
                        else:
                            break
                    
                    # Ensure the argument counts match
                    if len(args) != num_args:
                        raise TypeMismatchInExpression("at function call (argument count mismatch)")
                        
                    # Validate the type of each aggregated argument
                    for arg, param in zip(args, func_decl.params):
                        arg_type = self.visit(arg, o)

                        if type(arg_type) != type(param):
                            raise TypeMismatchInExpression("at function call")
                    
                    # Skip over the processed argument statements
                    i += 1 + len(args)
                    continue
                    
            # Normal visitation for unaffected nodes
            self.visit(stmt, o)
            i += 1

        # Use the local flag to safely determine if we should pop a scope
        if is_func_body:
            o["is_in_func"] += 1
        else:
            self.exit_scope(o)
            
        #print("Finished visiting BlockStmt node")

    def visit_var_decl(self, node: "VarDecl", o: Any = None):
        #print(f"Started visiting VarDecl node: {node.name}")
        #print(self.lookup(node.name, o))
        if node.name in o["scopes"][-1]:
            raise Redeclared("Variable", node.name)
        var_type = self.visit(node.var_type, o) if node.var_type is not None else None
        # Nếu có khởi tạo (vế phải)
        init_type = self.visit(node.init_value, o) if node.init_value else None
        if var_type is None and init_type is not None:
            var_type = init_type
        # --- XỬ LÝ ĐẶC BIỆT NẾU VẾ PHẢI LÀ STRUCT LITERAL ({...}) ---
        if isinstance(init_type, StructLiteral) and isinstance(var_type, StructType): 
            # Trường hợp: auto p = {10, 20}; -> Lỗi vì không biết struct nào
            
            # Lấy định nghĩa struct từ môi trường để kiểm tra fields
            struct_name = self.lookup(var_type.name, o)
            if struct_name not in o["structs"]:
                raise UndeclaredStruct(struct_name)
                
            struct_decl = o["structs"][struct_name]
            expected_types = [mem.type_spec for mem in struct_decl.body]
            
            # So khớp số lượng phần tử
            if len(init_type) != len(expected_types):
                raise TypeMismatchInStatement("Struct literal fields count mismatch")
            
            # So khớp kiểu của từng phần tử
            for t1, t2 in zip(init_type, expected_types):
                if type(t1) != type(t2):
                    raise TypeMismatchInStatement("Type mismatch in struct literal fields")
            
            # Nếu qua hết bước trên thì vế phải đã chuẩn
            init_type = var_type
            var_type = StructType(struct_name) # Gán kiểu struct cho biến

        # Lưu biến vào Scope
        #print(f"Variable '{node.name}' declared with type: {var_type} and initializer type: {init_type}")
        if type(init_type) != type(var_type) and init_type is not None and var_type is not None:
            raise TypeMismatchInStatement("at variable declaration")
        self.declare(node.name, var_type, o)
        #print(f"Finished visiting VarDecl node: {node.name}")

    def visit_if_stmt(self, node: "IfStmt", o: Any = None):
        #print("Started visiting IfStmt node")
        if not isinstance(self.visit(node.condition, o), IntType) :
            raise TypeMismatchInStatement("at if statement")
        self.visit(node.then_stmt, o)
        if node.else_stmt:
            self.visit(node.else_stmt, o)
        #print("Finished visiting IfStmt node")

    def visit_while_stmt(self, node, o):
        #print("Started visiting WhileStmt node") 
        o["in_loop"] += 1
        if not isinstance(self.visit(node.condition, o), IntType) :
            raise TypeMismatchInStatement("at while statement")
        self.visit(node.body, o)
        o["in_loop"] -= 1
        #print("Finished visiting WhileStmt node")


    def visit_for_stmt(self, node: "ForStmt", o: Any = None):
        #print("Started visiting ForStmt node")
        self.enter_scope(o)

        #print("Visiting for loop initialization")
        if node.init is not None:
            self.visit(node.init, o)

        #print("Visiting for loop condition")
        if node.condition is not None:
            if not isinstance(self.visit(node.condition, o), IntType):
                raise TypeMismatchInStatement("at for statement")
            self.visit(node.condition, o)

        #print("Visiting for loop update")
        if node.update is not None:
            self.visit(node.update, o)

        #print("Visiting for loop body")
        o["in_loop"] += 1
        self.visit(node.body, o)
        o["in_loop"] -= 1
        self.exit_scope(o)
        #print("Finished visiting ForStmt node")

    def visit_switch_stmt(self, node: "SwitchStmt", o: Any = None):
        #print("Started visiting SwitchStmt node")
        if not isinstance(self.visit(node.expr, o), IntType):
            raise TypeMismatchInStatement("at switch statement")
        o["in_switch"] += 1
        for case in node.cases:
            self.visit(case, o)
        if node.default_case:
            self.visit(node.default_case, o)
        o["in_switch"] -= 1
        #print("Finished visiting SwitchStmt node")

    def visit_case_stmt(self, node: "CaseStmt", o: Any = None):
        #print("Started visiting CaseStmt node")
        case_type = self.visit(node.expr, o)
        #print(f"Case value type: {case_type}")
        if not isinstance(case_type, IntType):
            raise TypeMismatchInStatement("at case statement")
        for stmt in node.statements:
            self.visit(stmt, o)
        #print("Finished visiting CaseStmt node")

    def visit_default_stmt(self, node: "DefaultStmt", o: Any = None):
        #print("Started visiting DefaultStmt node")
        for stmt in node.statements:
            self.visit(stmt, o)
        #print("Finished visiting DefaultStmt node")

    def visit_break_stmt(self, node: "BreakStmt", o: Any = None):
        #print("Started visiting BreakStmt node")
        if o["in_loop"] == 0 and o["in_switch"] == 0:
            raise MustInLoop("break")
        #print("Finished visiting BreakStmt node")

    def visit_continue_stmt(self, node: "ContinueStmt", o: Any = None):
        #print("Started visiting ContinueStmt node")
        if o["in_loop"] == 0:
            raise MustInLoop("continue")
        #print("Finished visiting ContinueStmt node")

    def visit_return_stmt(self, node: "ReturnStmt", o: Any = None):
        #print("Started visiting ReturnStmt node")
        #print(f"Current function return type: {o['current_return']}")
        expected_type = o["current_return"]
        actual_type = self.visit(node.expr, o) if node.expr else VoidType()
        if expected_type is not None:
            if type(actual_type) != type(expected_type):
                raise TypeMismatchInStatement("at return statement")

            # 3. If they are structs, make sure the struct names match
            if isinstance(actual_type, StructType) and isinstance(expected_type, StructType):
                name1 = getattr(actual_type, 'struct_name', getattr(actual_type, 'name', None))
                name2 = getattr(expected_type, 'struct_name', getattr(expected_type, 'name', None))
                if name1 != name2:
                    raise TypeMismatchInStatement("at return statement")
        #print("Finished visiting ReturnStmt node")

    def visit_expr_stmt(self, node: "ExprStmt", o: Any = None):
        #print(f"Started visiting ExprStmt node with expression: {node.expr}")
        expr_type = self.visit(node.expr, o)
        #print(f"Expression type: {expr_type}")
        if expr_type == "TYPE_MISMATCH":
            raise TypeMismatchInStatement("at assignment expression")
        #print("Finished visiting ExprStmt node")

    # Expressions
    def visit_binary_op(self, node: "BinaryOp", o: Any = None):
        #print(f"Started visiting BinaryOp node:{node.left} {node.operator} {node.right}")
        left_type = self.visit(node.left, o)
        right_type = self.visit(node.right, o)

        match node.operator:
            case "=":
                if left_type is None and right_type is None:
                    raise TypeCannotBeInferred(node.left)
            case "+" | "-" | "*" | "/" | "==" | "!=" | "<" | ">" | "<=" | ">=":
                if not ((isinstance(left_type, IntType) or isinstance(left_type, FloatType) or left_type == None) and (isinstance(right_type, IntType) or isinstance(right_type, FloatType) or right_type == None)):
                    raise TypeMismatchInExpression("at binary operation")
            case "%" | "&&" | "||" :
                if not (isinstance(left_type, IntType) and isinstance(right_type, IntType)):
                    raise TypeMismatchInExpression("at binary operation")
        #print(f"Left operand type: {left_type}, Right operand type: {right_type}")
        if (isinstance(left_type, IntType) and isinstance(right_type, IntType)) or (left_type is None and isinstance(right_type, IntType)) or (isinstance(left_type, IntType) and right_type is None):
            #print("Finished visiting BinaryOp node")
            return IntType()
        if (isinstance(left_type, FloatType) and isinstance(right_type, FloatType)) or (isinstance(left_type, IntType) and isinstance(right_type, FloatType)) or (isinstance(left_type, FloatType) and isinstance(right_type, IntType)) or (left_type is None and isinstance(right_type, FloatType)) or (isinstance(left_type, FloatType) and right_type is None):
            #print("Finished visiting BinaryOp node")    
            return FloatType()
        if left_type is None or right_type is None:
            raise TypeCannotBeInferred(node.left if left_type is None else node.right)
        raise TypeMismatchInExpression("Binary operator applied to incompatible types")
        
    

    def visit_prefix_op(self, node: "PrefixOp", o: Any = None):
        #print("Started visiting PrefixOp node")
        operand_type = self.visit(node.operand, o)
        if not isinstance(operand_type, IntType):
            raise TypeMismatchInExpression("at unary operation")
        #print("Finished visiting PrefixOp node")
        return operand_type

    def visit_postfix_op(self, node: "PostfixOp", o: Any = None):
        #print("Started visiting PostfixOp node")
        operand_type = self.visit(node.operand, o)
        if not isinstance(operand_type, IntType):
            raise TypeMismatchInExpression("at postfix operation")
        #print("Finished visiting PostfixOp node")
        return operand_type

    def visit_assign_stmt(self, node: "AssignStmt", o: Any = None):
        stmt_type = self.visit(node.stmt, o)
        if stmt_type == "TYPE_MISMATCH":
            raise TypeMismatchInStatement("at assignment statement")
        return stmt_type

    def visit_assign_expr(self, node: "AssignExpr", o: Any = None):
        #print("Started visiting AssignExpr node")
        # 1. Phải chắc chắn vế trái là Identifier hoặc MemberAccess
        if not (isinstance(node.lhs, Identifier) or isinstance(node.lhs, MemberAccess)):
            raise TypeMismatchInExpression("Left-hand side must be an identifier or member access")
            
        left_type = self.visit(node.lhs, o)
        right_type = self.visit(node.rhs, o)
        if (right_type == "TYPE_MISMATCH"):
            raise TypeMismatchInExpression("at assignment expression")
        #print(f"Left-hand side type: {left_type}, Right-hand side type: {right_type}")
        if left_type is None and right_type is None:
            raise TypeCannotBeInferred(right_type.name)
        # --- XỬ LÝ NẾU VẾ PHẢI LÀ STRUCT LITERAL ---
        if isinstance(right_type, list):
            if not isinstance(left_type, StructType):
                raise TypeMismatchInExpression("at assignment expression")

            struct_name = self.lookup(left_type, o)
            #print(f"Struct name for assignment: {struct_name}")
            struct_decl = o["structs"][struct_name]
            expected_types = [struct_decl[mem] for mem in struct_decl]
            
            if len(right_type) != len(expected_types):
                raise TypeMismatchInExpression("at assignment expression")
                
            for t1, t2 in zip(right_type, expected_types):
                if type(t1) != type(t2):
                    raise TypeMismatchInExpression("at assignment expression")
                    
            return left_type

        # --- XỬ LÝ GÁN BÌNH THƯỜNG ---
        if left_type is None:
            left_type = right_type
            self.declare(node.lhs.name, left_type, o) # Cập nhật kiểu cho identifier nếu nó chưa có kiểu
        #print(f"After type inference, Left-hand side type: {left_type}, Right-hand side type: {right_type}")
        if type(left_type) != type(right_type):
            #print("Type mismatch detected in assignment expression")
            return "TYPE_MISMATCH"
        if isinstance(left_type, StructType) and isinstance(right_type, StructType):
            name1 = getattr(left_type, 'struct_name', getattr(left_type, 'name', None))
            name2 = getattr(right_type, 'struct_name', getattr(right_type, 'name', None))
            if name1 != name2:
                #print("Struct type mismatch detected in assignment expression")
                return "TYPE_MISMATCH"
        #print("Finished visiting AssignExpr node")
        return left_type


    def visit_member_access(self, node: "MemberAccess", o: Any = None):
        # 1. Lấy kiểu của đối tượng (ví dụ lấy kiểu của 'p')
        #print("Started visiting MemberAccess node")
        obj_type = self.visit(node.obj, o)
        #print(f"Object type of member access: {obj_type}")
        # 2. Lấy tên struct (ví dụ: 'Point')
        struct_name = obj_type.struct_name if isinstance(obj_type, StructType) else None
        if struct_name is None:
            raise TypeMismatchInExpression("at member access")
        if struct_name not in o["structs"]:
            raise UndeclaredStruct(struct_name)
            
        # 3. Tìm member trong struct
        struct_decl = o["structs"][struct_name]
        # Giả sử struct_decl.body là danh sách các MemberDecl
        for mem in struct_decl:
            if mem == node.member:
                #print(f"Finished visiting MemberAccess node for member '{node.member}'")
                return struct_decl[mem] # Trả về kiểu của field đó
                
        raise TypeMismatchInExpression(f"at member access ({node.member} doesn't exist)")
    
    def visit_func_call(self, node: "FuncCall", o: Any = None):
        #print(f"Started visiting FuncCall node: {node.name}")
        if node.name not in o["functions"]:
            #print(f"Function '{node.name}' not found in environment")
            raise UndeclaredFunction(node.name)
        expected_params = o["functions"][node.name].params
        if len(node.args) != len(expected_params):
            raise TypeMismatchInExpression("at function call")
        for arg, param in zip(node.args, expected_params):
            arg_type = self.visit(arg, o)
            #print(f"Argument type: {arg_type}, Expected parameter type: {param.param_type}")
            if type(arg_type) != type(param.param_type):
                raise TypeMismatchInExpression("at function call")
        #print(f"Finished visiting FuncCall node: {node.name}")
        return o["functions"][node.name].return_type

    def visit_identifier(self, node: "Identifier", o: Any = None):
        #print(f"Started visiting Identifier node: {node.name}")
        identifier_type = self.lookup(node.name, o)
        if identifier_type == "Undeclared":
            if node.name in o["functions"]:
                return o["functions"][node.name].return_type
            raise UndeclaredIdentifier(node.name)
        return identifier_type

    def visit_struct_literal(self, node: "StructLiteral", o: Any = None):
        #print(f"Started visiting StructLiteral node")
        # 1. Khởi tạo mảng lưu kiểu của các phần tử bên trong {}
        element_types = []
        
        # 2. Duyệt qua từng biểu thức con (vd: node.values chứa [IntLiteral(10), FloatLiteral(20.5)])
        for expr in node.values:
            elem_type = self.visit(expr, o)
            element_types.append(elem_type)
        #print(f"Finished visiting StructLiteral node with element types: {element_types}")    
        # 3. Trả về danh sách type. Để các nút cha (Assign/VarDecl) tự đối chiếu.
        return StructLiteral(element_types)

    # Literals
    def visit_int_literal(self, node: "IntLiteral", o: Any = None):
        #print("Visiting IntLiteral node")
        return IntType()

    def visit_float_literal(self, node: "FloatLiteral", o: Any = None):
        #print("Visiting FloatLiteral node")
        return FloatType()

    def visit_string_literal(self, node: "StringLiteral", o: Any = None):
        #print("Visiting StringLiteral node")
        return StringType()

    def visit_param(self, node: "Param", o: Any = None):
        #print(f"Started visiting Param node: {node.name}")
        if node.name not in o["env"]:
            raise UndeclaredIdentifier(node.name)
        #print(f"Finished visiting Param node: {node.name}")
        return Param(self.lookup(node.name, o), node.name)
    
    # Helper methods
    def enter_scope(self, o):
        o["scopes"].append({}) # Changed from [] to {}

    def exit_scope(self, o):
        o["scopes"].pop()

    def declare(self, name, var_type, o): # Added var_type parameter
        if var_type is not None:
            self.visit(var_type, o) # Ensure the type is valid (e.g., struct type exists)
        if name in o["scopes"][-1] and o["scopes"][-1][name] is not None: # Check if already declared in current scope
            raise Redeclared("Variable", name)
        o["scopes"][-1][name] = var_type # Store the type in the dictionary

    def lookup(self, name, o):
        for scope in reversed(o["scopes"]):
            if name in scope:
                return scope[name] # Return the actual type object
        return "Undeclared"# Return None if not found