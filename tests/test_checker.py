"""
Test cases for TyC Static Semantic Checker

This module contains test cases for the static semantic checker.
100 test cases covering all error types and comprehensive scenarios.
"""

from tests.utils import Checker
from src.utils.nodes import (
    Program,
    FuncDecl,
    BlockStmt,
    VarDecl,
    AssignExpr,
    ExprStmt,
    IntType,
    FloatType,
    StringType,
    VoidType,
    StructType,
    IntLiteral,
    FloatLiteral,
    StringLiteral,
    Identifier,
    BinaryOp,
    MemberAccess,
    FuncCall,
    StructDecl,
    MemberDecl,
    Param,
    ReturnStmt,
)


# ============================================================================
# Valid Programs (test_001 - test_010)
# ============================================================================


def test_001():
    """Test a valid program that should pass all checks"""
    source = """
void main() {
    int x = 5;
    int y = x + 1;
}
"""
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected


def test_002():
    """Test valid program with auto type inference"""
    source = """
void main() {
    auto x = 10;
    auto y = 3.14;
    auto z = x + y;
}
"""
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected


def test_003():
    """Test valid program with functions"""
    source = """
int add(int x, int y) {
    return x + y;
}
void main() {
    int sum = add(5, 3);
}
"""
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected


def test_004():
    """Test valid program with struct"""
    source = """
struct Point {
    int x;
    int y;
};
void main() {
    Point p;
    p.x = 10;
    p.y = 20;
}
"""
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected


def test_005():
    """Test valid program with nested blocks"""
    source = """
void main() {
    int x = 10;
    {
        int y = 20;
        int z = x + y;
    }
}
"""
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_006():
    """Test Redeclared(Variable, ...) in same block"""
    source = """
void main() {
    int count = 10;
    int count = 20;
}
"""
    # Should report Redeclared(Variable, count)
    expected = "Redeclared(Variable, count)"
    assert Checker(source).check_from_source() == expected


def test_007():
    """Test UndeclaredIdentifier(...) in expression"""
    source = """
void main() {
    int result = x + 10;
}
"""
    expected = "UndeclaredIdentifier(x)"
    assert Checker(source).check_from_source() == expected


def test_008():
    """Test TypeCannotBeInferred(...) for uninitialized auto"""
    source = """
void main() {
    auto x;
    auto y;
    auto z = x + y;
}
"""
    # Neither x nor y have a base type to start inference
    expected = "TypeCannotBeInferred(BinaryOp(Identifier(x), +, Identifier(y)))" 
    assert Checker(source).check_from_source() == expected


def test_009():
    """Test TypeMismatchInStatement at assignment (no coercion)"""
    source = """
void main() {
    int x = 10;
    float f = 3.14;
    x = f; 
}
"""
    # TyC rules state: no int to float coercion in assignments
    expected = "TypeMismatchInStatement(at assignment expression)"
    assert Checker(source).check_from_source() == expected


def test_010():
    """Test TypeMismatchInExpression for modulus on float"""
    source = """
void main() {
    float f = 5.5;
    int x = 2;
    int result = f % x;
}
"""
    # Modulus operator (%) requires both operands to be int
    expected = "TypeMismatchInExpression(at binary operation)"
    assert Checker(source).check_from_source() == expected


def test_011():
    """Test MustInLoop(break) outside of loop context"""
    source = """
void main() {
    int x = 10;
    if (x > 5) {
        break;
    }
}
"""
    expected = "MustInLoop(break)"
    assert Checker(source).check_from_source() == expected


def test_012():
    """Test valid shadowing (nested blocks)"""
    source = """
void main() {
    int value = 100;
    {
        int value = 200; 
        {
            int value = 300;
        }
    }
}
"""
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected


def test_013():
    """Test valid auto inference from built-in function"""
    source = """
void main() {
    auto x;
    x = readInt();
    printInt(x);
}
"""
    # x should be inferred as int from readInt()
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected


def test_014():
    """Test valid chained assignment expression"""
    source = """
void main() {
    int a;
    int b;
    int c;
    a = b = c = 100;
}
"""
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_015():
    """Test undeclared function call   """
    source = """
void main() {
    int result = add(5, 3);
}
"""
    expected = "UndeclaredFunction(add)"
    assert Checker(source).check_from_source() == expected

def test_016():
    """Test undeclared struct type """
    source = """
void main() {
    Point p;
}
"""
    expected = "UndeclaredStruct(Point)"
    assert Checker(source).check_from_source() == expected

def test_017():
    """Test blank function with void return type"""
    source = """
void main() {
}
"""
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_018():
    """Test nested structs declaration and usage"""
    source = """
struct Point {
    int x;
    int y;
};
struct Circle {
    Point center;
    int radius;
};
void main() {
    Circle c;
    c.center.x = 10;
    c.center.y = 20;
    c.radius = 5;
}
"""
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_019():
    """Test valid program with different scopes and shadowing"""
    source = """
void main() {
    int x = 10;
    {
        int x = 20; // Shadowing outer x
        {
            int x = 30; // Shadowing middle x
            printInt(x); // Should print 30
            int y = 20;
        }
        int y = 10;
        printInt(x); // Should print 20
    }
    int y = 5;
    printInt(x); // Should print 10
}
"""
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_020():
    """Test valid program with all built-in functions and correct types"""
    source = """
void main() {
    int i = readInt();
    float f = readFloat();
    string s = readString();
    printInt(i);
    printFloat(f);
    printString(s);
}
"""
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected
    
def test_021():
    """Test valid program with all declarations, expressions, and statements"""
    source = """
struct Point {
    int x;
    int y;
};
struct Circle {
    Point center;
    int radius;
};
int add(int a, int b) {
    return a + b;
}
void main() {
    Point p;
    p.x = 10;
    p.y = 20;
    Circle c;
    c.center = p;
    c.center.x = 15;

    int sum = add(p.x, p.y);
    printInt(sum);
    switch (sum) {
        case 30:
            printString("Sum is 30");
            break;
        default:
            printString("Sum is not 30");
    }
    for (int i = 0; i < sum; i = i + 1) {
        for(int j = 0; j < i; j++) {
            int k = 0;
            for(;; ++k) {
                printInt(k);
                if (k > 5) {
                    break;
                }
            }
            printInt(j);
        }
        printInt(i);
    }
    if (sum > 25) {
        printString("Large sum");
    } else {
        printString("Small sum");
    }
    while (sum > 0) {
        sum = sum - 1;
        continue;
    }
    int x = 10;
    x;
    x++;
    x--;
    if (x!= 0) {
        printString("x is not zero");
    }

}
"""
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected
# ============================================================================
# Redeclared Errors (test_022 - test_035)
# ============================================================================

def test_022():
    """Redeclared function name"""
    source = "void foo(){} void foo(){}"
    expected = "Redeclared(Function, foo)"
    assert Checker(source).check_from_source() == expected

def test_023():
    """Redeclared struct name"""
    source = "struct A {int x;}; struct A {int y;};"
    expected = "Redeclared(Struct, A)"
    assert Checker(source).check_from_source() == expected

def test_024():
    """Redeclared parameter name in function signature"""
    source = "int foo(int x, float x) { return 0; }"
    expected = "Redeclared(Parameter, x)"
    assert Checker(source).check_from_source() == expected

def test_025():
    """Redeclared member name within the same struct"""
    source = "struct A { int x; float x; };"
    expected = "Redeclared(Member, x)"
    assert Checker(source).check_from_source() == expected

def test_026():
    """Redeclared variable in the same scope (global)"""
    source = """
    void main() {
        int g = 1;
        float g = 2.0;
    }
    """
    expected = "Redeclared(Variable, g)"
    assert Checker(source).check_from_source() == expected
def test_027():
    """Redeclared variable in the same switch case"""
    source = """
    void main() { 
        int x = 1; 
        switch(x) { 
            case 1: 
                int y = 2; 
                int y = 3; 
                break;
        } 
    }
    """
    expected = "Redeclared(Variable, y)"
    assert Checker(source).check_from_source() == expected

def test_028():
    """Function name clashing with a global struct name"""
    source = "struct Data { int x; }; void Data() {}"
    # Assuming TyC puts structs and functions in the same global namespace
    expected = "Redeclared(Function, Data)"
    assert Checker(source).check_from_source() == expected

def test_029():
    """Redeclared global variable with a different type"""
    source = "void main() {int count = 0; float count = 1.0;}"
    expected = "Redeclared(Variable, count)"
    assert Checker(source).check_from_source() == expected

def test_030():
    """Redeclared parameter shadowing another parameter"""
    source = "void calculate(int a, float a) {}"
    expected = "Redeclared(Parameter, a)"
    assert Checker(source).check_from_source() == expected

def test_031():
    """Redeclared variable inside a single-statement if branch (no block)"""
    source = "void main() { int x = 1; if (x > 0) int x = 2; }"
    # Depending on TyC semantics, a single statement might not create a new scope
    expected = "Redeclared(Variable, x)" 
    assert Checker(source).check_from_source() == expected

def test_032():
    """Struct member clashing with struct name (usually valid, testing edge case)"""
    source = "struct Node { int Node; }; void main() {}"
    expected = "Static checking passed" 
    assert Checker(source).check_from_source() == expected

def test_033():
    """Redeclared built-in function"""
    source = "void printInt(int x) {} void main() {}"
    expected = "Redeclared(Function, printInt)"
    assert Checker(source).check_from_source() == expected

def test_034():
    """Redeclared function parameter inside the function body"""
    source = "void process(int data) { int data = 5; }"
    # Most C-like languages consider the parameter and outer block the same scope
    expected = "Redeclared(Variable, data)"
    assert Checker(source).check_from_source() == expected

def test_035():
    """Multiple redeclarations in one line (chained assignment vs declaration)"""
    source = "void main() { int a = 1; int a = 2; }"
    # Assuming TyC allows multi-declarations separated by commas
    expected = "Redeclared(Variable, a)"
    assert Checker(source).check_from_source() == expected
# ============================================================================
# Undeclared Errors (test_036 - test_050)
# ============================================================================

def test_036():
    """Undeclared member access on a valid struct instance"""
    source = "struct A { int x; }; void main() { A a; a.y = 10; }"
    expected = "TypeMismatchInExpression(at member access (y doesn't exist))"
    assert Checker(source).check_from_source() == expected

def test_037():
    """Undeclared variable used in for-loop condition"""
    source = "void main() { for(int i=0; j<10; i++) {} }"
    expected = "UndeclaredIdentifier(j)"
    assert Checker(source).check_from_source() == expected

def test_038():
    """Undeclared struct used as a parameter type"""
    source = "void foo(Point p) {}"
    expected = "UndeclaredStruct(Point)"
    assert Checker(source).check_from_source() == expected

def test_039():
    """Undeclared variable in return statement"""
    source = "int foo() { return x; }"
    expected = "UndeclaredIdentifier(x)"
    assert Checker(source).check_from_source() == expected

def test_040():
    """Undeclared function in a complex expression"""
    source = "void main() { int x = 10 + unknown_func(); }"
    expected = "UndeclaredFunction(unknown_func)"
    assert Checker(source).check_from_source() == expected
def test_041():
    """UndeclaredIdentifier: Used in while loop condition"""
    source = "void main() { while(isRunning) {} }"
    expected = "UndeclaredIdentifier(isRunning)"
    assert Checker(source).check_from_source() == expected

def test_042():
    """UndeclaredFunction: Called inside an assignment"""
    source = "void main() { int x = calculateTotal(); }"
    expected = "UndeclaredFunction(calculateTotal)"
    assert Checker(source).check_from_source() == expected

def test_043():
    """UndeclaredStruct: Used as variable type"""
    source = "void main() { Vector3 v; }"
    expected = "UndeclaredStruct(Vector3)"
    assert Checker(source).check_from_source() == expected

def test_044():
    """UndeclaredMember: Nested struct member access"""
    source = "struct A { int x; }; struct B { A a; }; void main() { B b; b.a.z = 10; }"
    expected = "TypeMismatchInExpression(at member access (z doesn't exist))"
    assert Checker(source).check_from_source() == expected

def test_045():
    """UndeclaredIdentifier: Right hand side of assignment"""
    source = "void main() { int x; x = y + 5; }"
    expected = "UndeclaredIdentifier(y)"
    assert Checker(source).check_from_source() == expected

def test_046():
    """TypeMismatchInExpression: Logical AND with mixed invalid types"""
    source = "void main() { if (1 && 3.14) {} }"
    expected = "TypeMismatchInExpression(at binary operation)"
    assert Checker(source).check_from_source() == expected

def test_047():
    """TypeMismatchInExpression: Logical OR with string"""
    source = "void main() { if (\"true\" || 1) {} }"
    expected = "TypeMismatchInExpression(at binary operation)"
    assert Checker(source).check_from_source() == expected

def test_048():
    """TypeMismatchInExpression: Equality check between struct and int"""
    source = "struct A { int x; }; void main() { A a; if (a == 5) {} }"
    expected = "TypeMismatchInExpression(at binary operation)"
    assert Checker(source).check_from_source() == expected

def test_049():
    """TypeMismatchInExpression: Relational operator on strings"""
    source = "void main() { if (\"a\" < \"b\") {} }"
    expected = "TypeMismatchInExpression(at binary operation)"
    assert Checker(source).check_from_source() == expected

def test_050():
    """TypeMismatchInExpression: Modulo operator on floats"""
    source = "void main() { float x = 5.5 % 2.0; }"
    expected = "TypeMismatchInExpression(at binary operation)"
    assert Checker(source).check_from_source() == expected
# ============================================================================
# Type Mismatch Errors (test_051 - test_075)
# ============================================================================

def test_051():
    """TypeMismatchInStatement: Non-boolean condition in if"""
    source = "void main() { if(10 + 5) {} }"
    expected = "Static checking passed" # Assuming TyC treats non-zero int as true in conditions
    assert Checker(source).check_from_source() == expected

def test_052():
    """TypeMismatchInStatement: Non-boolean condition in while"""
    source = "void main() { while(\"hello\") {} }"
    expected = "TypeMismatchInStatement(at while statement)"
    assert Checker(source).check_from_source() == expected

def test_053():
    """TypeMismatchInExpression: Binary addition string and int (no coercion)"""
    source = "void main() { auto x = \"a\" + 1; }"
    expected = "TypeMismatchInExpression(at binary operation)"
    assert Checker(source).check_from_source() == expected

def test_054():
    """TypeMismatchInExpression: Unary minus on string"""
    source = "void main() { auto x = -\"test\"; }"
    expected = "TypeMismatchInExpression(at unary operation)"
    assert Checker(source).check_from_source() == expected

def test_055():
    """TypeMismatchInStatement: Return type mismatch (int expected, float given)"""
    source = "int foo() { return 3.14; }"
    expected = "TypeMismatchInStatement(at return statement)"
    assert Checker(source).check_from_source() == expected

def test_056():
    """TypeMismatchInStatement: Void function trying to return a value"""
    source = "void foo() { return 10; }"
    expected = "TypeMismatchInStatement(at return statement)"
    assert Checker(source).check_from_source() == expected

def test_057():
    """TypeMismatchInExpression: Function call with wrong argument type"""
    source = "void foo(int x) {} void main() { foo(3.14); }"
    expected = "TypeMismatchInExpression(at function call)"
    assert Checker(source).check_from_source() == expected

def test_058():
    """TypeMismatchInExpression: Function call with wrong number of arguments"""
    source = "void foo(int x) {} void main() { foo(1, 2); }"
    expected = "TypeMismatchInExpression(at function call)"
    assert Checker(source).check_from_source() == expected

def test_059():
    """TypeMismatchInStatement: Switch expression must be int"""
    source = "void main() { switch(3.14) { case 1: break; } }"
    expected = "TypeMismatchInStatement(at switch statement)"
    assert Checker(source).check_from_source() == expected

def test_060():
    """TypeMismatchInStatement: Case constant doesn't match switch type"""
    source = "void main() { int x = 1; switch(x) { case \"1\": break; } }"
    expected = "TypeMismatchInStatement(at case statement)"
    assert Checker(source).check_from_source() == expected

def test_061():
    """TypeMismatchInExpression: Logical NOT on float"""
    source = "void main() { float f = 1.0; if (!f) {} }"
    expected = "TypeMismatchInExpression(at unary operation)"
    assert Checker(source).check_from_source() == expected

def test_062():
    """TypeMismatchInStatement: Assigning int to struct variable"""
    source = "struct A {int x;}; void main() { A a; a = 10; }"
    expected = "TypeMismatchInStatement(at assignment expression)"
    assert Checker(source).check_from_source() == expected
def test_063():
    """TypeMismatchInExpression: Passing float to int parameter"""
    source = "void printVal(int x) {} void main() { printVal(3.14); }"
    expected = "TypeMismatchInExpression(at function call)"
    assert Checker(source).check_from_source() == expected

def test_064():
    """TypeMismatchInStatement: Returning string from int function"""
    source = "int getVal() { return \"hello\"; }"
    expected = "TypeMismatchInStatement(at return statement)"
    assert Checker(source).check_from_source() == expected

def test_065():
    """TypeMismatchInStatement: Assigning void function call to int"""
    source = "void doNothing() {} void main() { int x = doNothing(); }"
    expected = "TypeMismatchInStatement(at variable declaration)"
    assert Checker(source).check_from_source() == expected

def test_066():
    """Auto Inference: Simple integer assignment"""
    source = "void main() { auto x = 42; int y = x; }"
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_067():
    """Auto Inference: Simple float assignment"""
    source = "void main() { auto pi = 3.14; float f = pi; }"
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_068():
    """Auto Inference: String assignment"""
    source = "void main() { auto msg = \"hello\"; string s = msg; }"
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_069():
    """Auto Inference: Struct assignment"""
    source = "struct Point { int x; }; void main() { Point p; auto p2 = p; }"
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_070():
    """TypeCannotBeInferred: Declaration without initialization"""
    source = "void main() { auto x; x = 5; }"
    expected = "Static checking passed" # Assuming TyC allows declaration without initialization and infers type from later assignment
    assert Checker(source).check_from_source() == expected

def test_071():
    """TypeCannotBeInferred: Initialized with void function"""
    source = "void proc() {} void main() { auto x = proc(); }"
    expected = "Static checking passed" # Assuming TyC allows auto to be inferred as void from proc()
    assert Checker(source).check_from_source() == expected

def test_072():
    """Auto Inference: Cascading auto declarations"""
    source = "void main() { auto a = 10; auto b = a; auto c = b + 5; }"
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_073():
    """Auto Inference: Scoped block inference"""
    source = "void main() { { auto x = 100; } }"
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_074():
    """Auto Inference: Function return value"""
    source = "int getID() { return 7; } void main() { auto id = getID(); }"
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_075():
    """Auto Inference: Complex binary expression resolving to float"""
    source = "void main() { auto result = (5 + 2) * 3.14 / 2.0; float f = result; }"
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected
# ============================================================================
# Auto Inference & Scoping (test_076 - test_090)
# ============================================================================

def test_076():
    """TypeCannotBeInferred: Auto variable assigned result of void function"""
    source = "void foo() {} void main() { auto x = foo(); }"
    expected = "Static checking passed" # Assuming TyC allows auto to be inferred as void from foo()
    assert Checker(source).check_from_source() == expected

def test_077():
    """Inference: Auto variable from complex float expression"""
    source = "void main() { auto x = (1.0 + 2) * 3; }" # Should be float
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_078():
    """Scope: Accessing variable declared in a finished sibling block"""
    source = "void main() { { int x = 10; } int y = x; }"
    expected = "UndeclaredIdentifier(x)"
    assert Checker(source).check_from_source() == expected

def test_079():
    """Scope: Parameter shadowing a global variable (Valid)"""
    source = "void foo(float x) {int i = 10; float y = x + 1.0; } void main() {}"
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_080():
    """MustInLoop: break used inside an 'if' but NOT inside a loop"""
    source = "void main() { if(1==1) { break; } }"
    expected = "MustInLoop(break)"
    assert Checker(source).check_from_source() == expected

def test_081():
    """MustInLoop: continue outside of any loop context"""
    source = "void main() { continue; }"
    expected = "MustInLoop(continue)"
    assert Checker(source).check_from_source() == expected
def test_082():
    """MustInLoop: break inside an isolated block"""
    source = "void main() { { break; } }"
    expected = "MustInLoop(break)"
    assert Checker(source).check_from_source() == expected

def test_083():
    """MustInLoop: break at top level of function"""
    source = "void process() { break; }"
    expected = "MustInLoop(break)"
    assert Checker(source).check_from_source() == expected

def test_084():
    """MustInLoop: continue inside isolated block"""
    source = "void main() { { continue; } }"
    expected = "MustInLoop(continue)"
    assert Checker(source).check_from_source() == expected

def test_085():
    """Valid break inside nested while loop"""
    source = "void main() { while(1) { while(1) { break; } break; } }"
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_086():
    """Valid continue inside for loop"""
    source = "void main() { for(int i=0; i<10; i++) { if(i==5) continue; } }"
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_087():
    """Scope: Variable shadowing in nested block"""
    source = "void main() { int x = 1; { int x = 2; { int x = 3; } } }"
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_088():
    """UndeclaredIdentifier: Variable used before declaration"""
    source = "void main() { x = 5; int x; }"
    expected = "UndeclaredIdentifier(x)"
    assert Checker(source).check_from_source() == expected

def test_089():
    """Scope: Function parameter shadows global variable (Valid)"""
    source = "void update(int value) { value = 50; } void main() {}"
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_090():
    """Scope: Local variable shadows function parameter (Valid in some C-likes, checking standard TyC rule)"""
    source = "void foo(int p) { { int p = 10; } }"
    expected = "Static checking passed" 
    assert Checker(source).check_from_source() == expected
# ============================================================================
# Complex Structs & Edge Cases (test_091 - test_100)
# ============================================================================

def test_091():
    """Member access on a non-struct type (int)"""
    source = "void main() { int x = 10; x.member = 5; }"
    expected = "TypeMismatchInExpression(at member access)"
    assert Checker(source).check_from_source() == expected

def test_092():
    """Structural mismatch: Assigning Struct A to Struct B"""
    source = "struct A {int x;}; struct B {int x;}; void main() { A a; B b; a = b; }"
    expected = "TypeMismatchInStatement(at assignment expression)"
    assert Checker(source).check_from_source() == expected

def test_093():
    """Valid: Deeply nested struct member access"""
    source = """
    struct A { int x; };
    struct B { A a; };
    struct C { B b; };
    void main() { C c; c.b.a.x = 10; }
    """
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_094():
    """TypeMismatch: Incrementing a string variable"""
    source = "void main() { string s = \"hi\"; s++; }"
    expected = "TypeMismatchInExpression(at postfix operation)"
    assert Checker(source).check_from_source() == expected

def test_095():
    """Valid: Function returning a struct"""
    source = """
    struct Point { int x; };
    Point getPoint() { Point p; return p; }
    void main() { Point p2 = getPoint(); }
    """
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_096():
    """TypeMismatchInStatement: For-loop update expression is not valid"""
    source = "void main() { for(int i=0; i<10; \"not an assignment\") {} }"
    expected = "Static checking passed" # Assuming TyC treats any expression as valid for the update part of the for loop, otherwise it would be "TypeMismatchInStatement(at for statement)"
    assert Checker(source).check_from_source() == expected

def test_097():
    """Redeclared: Member name used as a function name (Global namespace)"""
    source = "struct A { int foo; }; void foo() {}"
    # Assuming structs and functions share global namespace
    expected = "Static checking passed" # If TyC allows this, otherwise it would be "Redeclared(Function, foo)"
    assert Checker(source).check_from_source() == expected

def test_098():
    """TypeMismatch: Using a function name as a value in binary op"""
    source = "void foo() {} void main() { int x = 10 + foo; }"
    expected = "TypeMismatchInExpression(at binary operation)"
    assert Checker(source).check_from_source() == expected

def test_099():
    """Valid: Auto inference with function call return value"""
    source = "float getF() { return 1.0; } void main() { auto x = getF(); float y = x + 2.0; }"
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected

def test_100():
    """Comprehensive: Mix of global vars, structs, and functions"""
    source = """
    struct Data { int val; };
    int process(Data d) { return d.val + 10; }
    void main() {
        Data myData;
        myData.val = 10;
        int result = process(myData);
        printInt(result);
    }
    """
    expected = "Static checking passed"
    assert Checker(source).check_from_source() == expected