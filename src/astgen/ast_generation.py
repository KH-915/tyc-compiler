"""
AST Generation module for TyC programming language.
This module contains the ASTGeneration class that converts parse trees
into Abstract Syntax Trees using the visitor pattern.
"""

from ...build.TyCVisitor import TyCVisitor
from ...build.TyCParser import TyCParser
from ..utils.nodes import *


class ASTGeneration(TyCVisitor):
    """AST Generation visitor for TyC language."""

    # ---------- PROGRAM ----------

    def visitProgram(self, ctx: TyCParser.ProgramContext):
        decls = []
        for i in range(ctx.getChildCount() - 1):
            child = ctx.getChild(i)
            decls.append(self.visit(child))
        return Program(decls)

    # ---------- STRUCT ----------

    def visitStructDecl(self, ctx: TyCParser.StructDeclContext):
        name = ctx.ID().getText()
        members = [self.visit(m) for m in ctx.structMember()]
        return StructDecl(name, members)

    def visitStructMember(self, ctx: TyCParser.StructMemberContext):
        type_spec = self.visit(ctx.typeSpec())
        name = ctx.ID().getText()
        return MemberDecl(type_spec, name)

    # ---------- FUNCTION ----------

    def visitTypeFuncDecl(self, ctx: TyCParser.TypeFuncDeclContext):
        return_type = self.visit(ctx.typeSpec())
        name = ctx.ID().getText()
        params = self.visit(ctx.paramList()) if ctx.paramList() else []
        body = self.visit(ctx.block())
        return FuncDecl(return_type, name, params, body)

    def visitInferredFuncDecl(self, ctx: TyCParser.InferredFuncDeclContext):
        # Using None for inferred functions to match test_033
        return_type = None
        name = ctx.ID().getText()
        params = self.visit(ctx.paramList()) if ctx.paramList() else []
        body = self.visit(ctx.block())
        return FuncDecl(return_type, name, params, body)

    def visitParamList(self, ctx: TyCParser.ParamListContext):
        return [self.visit(p) for p in ctx.param()]

    def visitParam(self, ctx: TyCParser.ParamContext):
        return Param(self.visit(ctx.typeSpec()), ctx.ID().getText())

    # ---------- BLOCK / STMT ----------

    def visitBlock(self, ctx: TyCParser.BlockContext):
        return BlockStmt([self.visit(s) for s in ctx.stmt()])

    def visitStmt(self, ctx: TyCParser.StmtContext):
        # Handle the new standalone 'expr SEMI' rule
        if ctx.expr():
            return ExprStmt(self.visit(ctx.expr()))
        # Otherwise, visit the specific stmt type (ifStmt, whileStmt, etc.)
        return self.visit(ctx.getChild(0))

    def visitVarDecl(self, ctx: TyCParser.VarDeclContext):
        var_type = self.visit(ctx.typeSpec())
        name = ctx.ID().getText()
        # Initializer is now just an 'expr' in the grammar
        init_value = self.visit(ctx.expr()) if ctx.expr() else None
        return VarDecl(var_type, name, init_value)

    def visitLhs(self, ctx: TyCParser.LhsContext):
        if ctx.DOT():
            return MemberAccess(Identifier(ctx.ID(0).getText()), ctx.ID(1).getText())
        return Identifier(ctx.ID(0).getText())

    # ---------- CONTROL FLOW ----------

    def visitIfStmt(self, ctx: TyCParser.IfStmtContext):
        condition = self.visit(ctx.expr())
        then_stmt = self.visit(ctx.stmt(0))
        else_stmt = self.visit(ctx.stmt(1)) if ctx.stmt(1) else None
        return IfStmt(condition, then_stmt, else_stmt)

    def visitWhileStmt(self, ctx: TyCParser.WhileStmtContext):
        condition = self.visit(ctx.expr())
        body = self.visit(ctx.stmt())
        return WhileStmt(condition, body)

    def visitForStmt(self, ctx: TyCParser.ForStmtContext):
        init = self.visit(ctx.forInit()) if ctx.forInit() else None
        condition = self.visit(ctx.expr()) if ctx.expr() else None
        update = self.visit(ctx.forUpdate()) if ctx.forUpdate() else None
        body = self.visit(ctx.stmt())
        return ForStmt(init, condition, update, body)

    def visitForInit(self, ctx: TyCParser.ForInitContext):
        if ctx.AUTO():
            name = ctx.ID().getText()
            init_value = self.visit(ctx.expr())
            return VarDecl(None, name, init_value)
        # It's an expression (assignment, etc.)
        return self.visit(ctx.expr())

    def visitForUpdate(self, ctx: TyCParser.ForUpdateContext):
        return self.visit(ctx.expr())

    def visitSwitchStmt(self, ctx: TyCParser.SwitchStmtContext):
        expr = self.visit(ctx.expr())
        cases = [self.visit(c) for c in ctx.caseBlock()]
        default_case = self.visit(ctx.defaultBlock()) if ctx.defaultBlock() else None
        return SwitchStmt(expr, cases, default_case)

    def visitCaseBlock(self, ctx: TyCParser.CaseBlockContext):
        # Case labels can now be expressions (e.g. 1 + 2)
        expr = self.visit(ctx.expr())
        statements = [self.visit(s) for s in ctx.stmt()]
        return CaseStmt(expr, statements)

    def visitDefaultBlock(self, ctx: TyCParser.DefaultBlockContext):
        statements = [self.visit(s) for s in ctx.stmt()]
        return DefaultStmt(statements)

    def visitBreakStmt(self, ctx: TyCParser.BreakStmtContext):
        return BreakStmt()

    def visitContinueStmt(self, ctx: TyCParser.ContinueStmtContext):
        return ContinueStmt()

    def visitReturnStmt(self, ctx: TyCParser.ReturnStmtContext):
        expr = self.visit(ctx.expr()) if ctx.expr() else None
        return ReturnStmt(expr)

    # ---------- EXPRESSIONS ----------

    def visitExpr(self, ctx: TyCParser.ExprContext):
        # Top level expression handles Right-Associative Assignments
        if ctx.ASSIGN():
            lhs_node = self.visit(ctx.lhs())
            rhs_node = self.visit(ctx.expr())
            return AssignExpr(lhs_node, rhs_node)
        return self.visit(ctx.expr0())

    def visitExpr0(self, ctx: TyCParser.Expr0Context):
        # Logical OR shifted down to expr0
        if ctx.getChildCount() == 1:
            return self.visit(ctx.expr1())
        left = self.visit(ctx.expr0())
        right = self.visit(ctx.expr1())
        return BinaryOp(left, '||', right)

    def visitExpr1(self, ctx: TyCParser.Expr1Context):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.expr2())
        left = self.visit(ctx.expr1())
        right = self.visit(ctx.expr2())
        return BinaryOp(left, '&&', right)

    def visitExpr2(self, ctx: TyCParser.Expr2Context):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.expr3())
        left = self.visit(ctx.expr2())
        op = '==' if ctx.EQ() else '!='
        right = self.visit(ctx.expr3())
        return BinaryOp(left, op, right)

    def visitExpr3(self, ctx: TyCParser.Expr3Context):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.expr4())
        left = self.visit(ctx.expr3())
        if ctx.LT(): op = '<'
        elif ctx.LE(): op = '<='
        elif ctx.GT(): op = '>'
        else: op = '>='
        right = self.visit(ctx.expr4())
        return BinaryOp(left, op, right)

    def visitExpr4(self, ctx: TyCParser.Expr4Context):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.expr5())
        left = self.visit(ctx.expr4())
        op = '+' if ctx.ADD() else '-'
        right = self.visit(ctx.expr5())
        return BinaryOp(left, op, right)

    def visitExpr5(self, ctx: TyCParser.Expr5Context):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.expr6())
        left = self.visit(ctx.expr5())
        if ctx.MUL(): op = '*'
        elif ctx.DIV(): op = '/'
        else: op = '%'
        right = self.visit(ctx.expr6())
        return BinaryOp(left, op, right)

    def visitExpr6(self, ctx: TyCParser.Expr6Context):
        if ctx.expr7():
            return self.visit(ctx.expr7())
        # Prefix operators
        op = ctx.getChild(0).getText()
        operand = self.visit(ctx.expr6())
        return PrefixOp(op, operand)

    def visitExpr7(self, ctx: TyCParser.Expr7Context):
        base = self.visit(ctx.operand())
        if ctx.INC():
            return PostfixOp('++', base)
        if ctx.DEC():
            return PostfixOp('--', base)
        return base

    # ---------- OPERAND LABELS ----------

    def visitLiteralOperand(self, ctx: TyCParser.LiteralOperandContext):
        return self.visit(ctx.literal())

    def visitLhsOperand(self, ctx: TyCParser.LhsOperandContext):
        return self.visit(ctx.lhs())

    def visitFunctionCallOperand(self, ctx: TyCParser.FunctionCallOperandContext):
        name = ctx.ID().getText()
        args = [self.visit(e) for e in ctx.argList().expr()] if ctx.argList() else []
        return FuncCall(name, args)

    def visitParenthesizedOperand(self, ctx: TyCParser.ParenthesizedOperandContext):
        return self.visit(ctx.expr())

    def visitStructLiteralOperand(self, ctx: TyCParser.StructLiteralOperandContext):
        # Handles Point p = {10, 20}; 
        args = [self.visit(e) for e in ctx.argList().expr()] if ctx.argList() else []
        return StructLiteral(args)

    # ---------- LITERALS ----------

    def visitLiteral(self, ctx: TyCParser.LiteralContext):
        if ctx.INTLIT():
            return IntLiteral(int(ctx.INTLIT().getText()))
        if ctx.FLOATLIT():
            return FloatLiteral(float(ctx.FLOATLIT().getText()))
        if ctx.STRINGLIT():
            return StringLiteral(ctx.STRINGLIT().getText())
        if ctx.BOOLLIT():
            # Standard workaround: bool as int (1/0) because nodes.py lacks BoolLiteral
            val = 1 if ctx.BOOLLIT().getText() == 'true' else 0
            return IntLiteral(val)
        return None

    # ---------- TYPE ----------

    def visitTypeSpec(self, ctx: TyCParser.TypeSpecContext):
        if ctx.INT(): return IntType()
        if ctx.FLOAT(): return FloatType()
        if ctx.STRING(): return StringType()
        if ctx.VOID(): return VoidType()
        if ctx.BOOL(): return IntType() # No BoolType in nodes.py
        if ctx.AUTO(): return None
        if ctx.ID(): return StructType(ctx.ID().getText())
        return None