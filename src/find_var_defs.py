from utils import *


def get_var_decs_from_catch_clause(catch_node):
    output = []
    if len(catch_node.children) < 2 and set(['type.UnionType']) & catch_node.children[0].labels:
        types = []
        name_node = None
        for child_node in catch_node.children[0].children:
            if 'type.ClassOrInterfaceType' in child_node.labels:
                types.append(child_node)
            else:
                name_node = child_node
                break
        if name_node:
            output.append((name_node, types[0], None, catch_node))
    else:
        type_node = catch_node.children[0]
        name_node = catch_node.children[1]
        output.append((name_node, type_node, None, catch_node))
    return output

def get_variable_scope(def_node, root_node):
    path = build_path(def_node, root_node)
    for index in xrange(len(path) - 1, -1, -1):
        node = path[index]
        if node.labels & set(['stmt.ForeachStmt', 'stmt.IfStmt', 'stmt.WhileStmt',   'stmt.BlockStmt', 'body.ClassOrInterfaceDeclaration',
                              "body.MethodDeclaration", "body.ConstructorDeclaration",
                              'body.EnumDeclaration', 'body.ClassDeclaration',
                              'body.InterfaceDeclaration', "stmt.CatchClause",
                              'stmt.IfStmt', 'stmt.ForeachStmt', 'stmt.LabeledStmt', 'stmt.AssertStmt',
                              'stmt.ContinueStmt', 'stmt.DoStmt', 'stmt.CatchClause', 'stmt.WhileStmt',
                              'stmt.ThrowStmt', 'stmt.SynchronizedStmt', 'stmt.LocalClassDeclarationStmt',
                              'stmt.ReturnStmt', 'stmt.TryStmt', 'stmt.EmptyStmt', 'stmt.ForStmt',
                              'stmt.SwitchEntryStmt', 'stmt.SwitchStmt', 'stmt.BlockStmt', 'stmt.BreakStmt',
                              'stmt.ExplicitConstructorInvocationStmt']):
            return node
    raise Exception("Can't find var scope")

def get_var_decs_from_var_def(def_node, class_node, source):
    output = []
    if not def_node.children:
        # ['stmt.CatchClause', 'body.Parameter'] case
        return []
    type_node_index = 0
    while set(['expr.NormalAnnotationExpr', 'expr.MarkerAnnotationExpr', 'expr.SingleMemberAnnotationExpr']) & def_node.children[type_node_index].labels:
        type_node_index += 1
    type_node = None
    while type_node_index < len(def_node.children) and \
            set(['type.ClassOrInterfaceType', 'type.ArrayType', 'type.PrimitiveType']) & def_node.children[type_node_index].labels:
        type_node = def_node.children[type_node_index] #we select only one
        type_node_index += 1
    type_node_index -= 1
    if not type_node:
        raise Exception("unknown var decl format", "no type_node")

    var_name = None
    if 'type.ArrayType' in type_node.labels:
        while len(type_node.children) == 1 and 'type.ArrayType' in type_node.children[0].labels:
            type_node = type_node.children[0]
        if len(type_node.children) == 2:
            var_name = type_node.children[1]
            type_node = type_node.children[0]
            val_node = None
            if type_node_index == len(def_node.children) - 2:
                val_node = def_node.children[len(def_node.children) - 1]
                delimiter = source[ var_name.end:val_node.start].strip()
                delimiter = delimiter.replace("[]", " ").strip()
                if delimiter != "=":
                    raise Exception("unknown var decl format", "array type variable value problem")
            elif type_node_index < len(def_node.children) - 2:
                raise Exception("unknown var decl format", "array type variable and something after it")
            return [(var_name, type_node, val_node, get_variable_scope(def_node, class_node))]
    if not type_node:
        raise Exception("unknown var definition format", def_node.children[type_node_index].get_snippet(source))

    for var_decl_node_index in xrange(type_node_index + 1, len(def_node.children)):
        var_decl_node = def_node.children[var_decl_node_index]
        if "expr.SimpleName" in var_decl_node.labels:
            output.append((var_decl_node, type_node, None, get_variable_scope(def_node, class_node)))
        elif 'body.VariableDeclarator' in var_decl_node.labels:
            elems = var_decl_node.children
            elems = [elem for elem in elems if not COMMENTS_LABELS & elem.labels]
            if len(elems) != 2:
                raise Exception("unknown var definition format", "len(var_decl_node.children) != 2")
            var_name = elems[0]
            value_node = elems[1]
            #print value_node.get_snippet(source)
            #print "----"
            output.append((var_name, type_node, value_node, get_variable_scope(def_node, class_node)))
        elif 'stmt.BlockStmt' in var_decl_node.labels:
            break
        else:
            raise Exception("unknown var definition format", def_node.children[type_node_index].get_snippet(source))
    if not output:
        raise Exception("unknown var definition format", "did not find variables")
    return output

def get_enum_val_declaration(node, class_node, source):
    if not "body.EnumDeclaration" in class_node.labels:
        return []
    #TODO: extract default values as well
    name_node = node
    while name_node.children:
        for child in name_node.children:
            if 'expr.MarkerAnnotationExpr' in child.labels:
                continue
            name_node = child
            break
    return [(name_node, None, None, class_node)]


""" find all places with varialbe declarations and attach it to a certain scope of visibility """
def find_all_var_declarations(class_node, source):
    var_decs = []
    def process(stack):
        node = stack[-1]
        if node != class_node and node.labels & set(['body.ClassOrInterfaceDeclaration', 'body.EnumDeclaration',
                                                     'body.ClassDeclaration', 'body.InterfaceDeclaration',
                                                     'body.AnnotationDeclaration']):
            return False
        if "stmt.CatchClause" in node.labels:
            for item in get_var_decs_from_catch_clause(node):
                var_decs.append(item)
        elif ("expr.VariableDeclarationExpr" in node.labels or
                      'body.Parameter' in node.labels or
                      "body.FieldDeclaration" in node.labels):
            for item in get_var_decs_from_var_def(node, class_node, source):
                var_decs.append(item)
        elif 'body.EnumConstantDeclaration' in node.labels:
            for item in get_enum_val_declaration(node, class_node, source):
                var_decs.append(item)
        return True
    class_node.DFS1([], process)
    to_remove = []
    for first in xrange(len(var_decs)):
        for second in xrange(first + 1, len(var_decs)):
            if var_decs[first][0] == var_decs[second][0]:
                to_remove.append(second)
    var_decs = [var_decs[index] for index in xrange(len(var_decs)) if not index in to_remove]
    return var_decs