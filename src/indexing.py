from utils import *
from type_inference import *
from find_var_defs import find_all_var_declarations

import pickle

def collect_indexing_data_impl(fname, nodes, all_packages, all_classes_decls, all_methods, all_names, all_public_vars):
    source = open(fname).read()
    for node in all_nodes(nodes):
        if set(["expr.SimpleName", "expr.NameExpr"]) & node.labels:
            all_names.add(node.get_snippet(source))

    class_labels = set(['body.ClassOrInterfaceDeclaration', 'body.EnumDeclaration',
                        'body.ClassDeclaration', 'body.InterfaceDeclaration', 'body.AnnotationDeclaration'])
    classes = []
    for node in all_nodes(nodes):
        if node.labels & class_labels:
            classes += [node]
    package_name = get_package(source, nodes) or "<UNKNOWN_PACKAGE>"
    if package_name:
        all_packages.add(package_name)
    imports = get_imports(source, nodes)
    imports = [imported.replace(".*", "").strip() for imported in imports]
    for class_node in classes:
        class_name, type_parameters_parsed, extends_parsed_strs = parse_class_declaration(class_node, source)
        encaps_classes = [other_class_node for other_class_node in classes \
                   if other_class_node.start < class_node.start and other_class_node.end >= class_node.end]
        encaps_classes = sorted(encaps_classes, key=lambda class_node: class_node.start)
        full_name = [package_name] + [parse_class_declaration(encaps_class, source)[0].get_snippet(source) \
                                                 for encaps_class in encaps_classes] + [class_name.get_snippet(source)]
        full_name = ".".join(full_name)
        variables = find_all_var_declarations(class_node, source)
        for var_name, type_node, value_node, var_scope in variables:
            if var_scope == class_node:
                var_full_path = full_name +  "." + var_name.get_snippet(source)
                all_public_vars[var_full_path] = (var_name,
                                                  type_node,
                                                  (type_node and type_node.get_snippet(source)) or None,
                                                  value_node,
                                                  fname)
        for node in class_node.children:
            if set(["body.MethodDeclaration", "body.ConstructorDeclaration"]) & node.labels:
                return_type, method_name, params, output_type_params = parse_method_declaration(class_node, node, source)
                method_full_name = full_name + "." + method_name.get_snippet(source)
                all_methods[method_full_name] = (len(params), fname)
        type_param_names = set([type_param.get_snippet(source) for type_param, _ in type_parameters_parsed])
        all_classes_decls[full_name] =  (type_param_names,
                                         package_name,
                                         imports,
                                         extends_parsed_strs,
                                         (class_node.start, class_node.end, fname))


if __name__ == "__main__":
    import sys
    import os
    import pickle
    try:
        _, sources_root_folder, index_folder = sys.argv[:3]
        build_dump = "-d" in sys.argv
    except:
        print "usage: python indexing.py <root folder of java sources> <folder for indices> [-d]"
        exit()


    sources_fnames = [fname for fname in collect_java_sources(sources_root_folder)]
    print "source files:", len(sources_fnames)
    print """building asts"""
    fname2ast_loc = {}
    BATCH_SIZE = 1000
    index = 0
    for batch_start in xrange(0, len(sources_fnames), BATCH_SIZE):
        print "\tbatch", batch_start, "-", batch_start + BATCH_SIZE
        for fname, root_node in build_asts(sources_fnames[batch_start:batch_start + BATCH_SIZE]):
            index += 1
            coded = str(fname2code(fname)) + "_" + str(index)
            ast_loc = os.path.join(index_folder, coded + ".ast")
            out = open(ast_loc, "wb")
            pickle.dump((fname, root_node), out)
            out.close()
            fname2ast_loc[fname] = ast_loc
        break

    all_packages = set()
    all_classes_decls = {}
    all_methods = {}
    all_names = set()
    all_public_vars = {}
    class2parents = {}
    full_type_markup = {}


    paths = [("", os.path.join(index_folder, path)) for path in os.listdir(index_folder)]

    print """initial data collect"""
    for fname, ast_loc in fname2ast_loc.items():
        fname, root = pickle.load(open(ast_loc, "rb"))
        collect_indexing_data_impl(fname, root, all_packages, all_classes_decls, all_methods, all_names, all_public_vars)

    print """infer full types of classes' parents"""
    for class_full_name, (type_param_names, package_name, imports, extends_parsed_strs, fname) in all_classes_decls.items():
        extends_parsed_strs = [get_full_type_of_extends(extended_class_name,
                                                        package_name,
                                                        class_full_name,
                                                        imports,
                                                        all_classes_decls)
                                        for extended_class_name in extends_parsed_strs]
        extends_parsed_strs = [value for value in extends_parsed_strs if value]
        if extends_parsed_strs:
            class2parents[class_full_name] = extends_parsed_strs

    print """temporary methods index"""
    method_name2full_names = {}
    for method_full_name in all_methods.keys():
        method_name = method_full_name.split(".")[-1]
        method_name2full_names.setdefault(method_name, []).append(method_full_name)

    print """inferring full types of classes' properties"""
    for fname, ast_loc in fname2ast_loc.items():
        fname, root = pickle.load(open(ast_loc, "rb"))
        infer_types_of_class_properties(fname, root, all_packages, all_names, all_public_vars, all_methods, all_classes_decls)

    print """inferring full types of variables"""
    var_types_inference_stat = [0, 0, 0, 0]
    for fname, ast_loc in fname2ast_loc.items():
        fname, root = pickle.load(open(ast_loc, "rb"))
        infer_types_of_vars_impl(fname, root, all_packages, all_names, all_public_vars,
                                 all_methods, method_name2full_names, class2parents, all_classes_decls,
                                 full_type_markup, var_types_inference_stat)

    print "uniq names", len(all_names)
    print "class fields", len(all_public_vars)
    print "class methods", len(all_methods)
    print "classes with defined parent classes", len(class2parents)
    print "total class delcarations", len(all_classes_decls)

    print """saving"""
    pickle.dump([fname2ast_loc,
                 all_names,
                 all_packages,
                 all_classes_decls,
                 all_methods,
                 all_public_vars,
                 class2parents,
                 full_type_markup], open(os.path.join(index_folder, "source_index.b"), "wb"))

    if build_dump:
        print """building dump for comparison tests"""
        dump = open(os.path.join(index_folder, "dump.txt"), "w")
        dump.write("PACKAGES\n")
        for package in sorted(list(all_packages)):
            dump.write(package + "\n")
        dump.write("CLASS_DECLS\n")
        for full_class_name in sorted(all_classes_decls.keys()):
            dump.write(full_class_name + "\n")
            type_param_names, package_name, imports, extends_parsed_strs, (start, end, fname) = all_classes_decls[full_class_name]
            dump.write("TYPEPARAMS: " + " ".join(sorted(list(type_param_names))) + "\n")
            dump.write("PACKAGE: " + package_name + "\n")
            dump.write("IMPORTS: " + " ".join(sorted(list(imports))) + "\n")
            dump.write("EXTENDS: " + " ".join(sorted(list(extends_parsed_strs))) + "\n")
            dump.write("LOC: " + str(start) + ":"  + str(end) + ":" + fname + "\n")

        dump.write("METHODS\n")
        for method_full_name in sorted(all_methods.keys()):
            param_count, fname = all_methods[method_full_name]
            dump.write(method_full_name + " " + str(param_count) + " " + fname + "\n")

        dump.write("PUBLICVARS\n")
        for var_full_path in sorted(all_public_vars.keys()):
            var_name, type_node, full_type, value_node, fname = all_public_vars[var_full_path]
            dump.write(var_full_path + " " + str(full_type) + " " + str(value_node and value_node.start or -1) \
                                                                + " " + str(value_node and value_node.end or -1) + "\n")

        dump.write("CLASS2PARENTS\n")
        for full_class_name in sorted(class2parents.keys()):
            extends = class2parents[full_class_name]
            dump.write(full_class_name + " " + " ".join(sorted(extends)) + "\n")

        dump.write("VAR_TYPES\n")
        for fname, start, end in sorted(full_type_markup.keys()):
            value = full_type_markup[(fname, start, end)]
            if type(value) == tuple:
                value = value[0]
            dump.write(fname + ":" + str(start) + ":" + str(end) + " " + str(value) + "\n")
        dump.close()

    print "done"



