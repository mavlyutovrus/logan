from utils import *
from find_var_defs import find_all_var_declarations


def get_full_type_of_extends(type_snippet,
                             package_name,
                             class_full_name,
                             imports,
                             all_defined_classes, defined_classes_by_prefix, defined_classes_by_suffix):

    type_snippet = type_snippet.split("<")[0] \
        .replace("[]", "") \
        .replace("\n", "").replace("\t", "") \
        .replace(" ", "").strip()
    full_type = None

    if not full_type:
        full_class_name_chunks = class_full_name.split(".")
        for cut in xrange(len(full_class_name_chunks), -1, -1):
            parent = ".".join(full_class_name_chunks[:cut])
            if not parent in all_defined_classes:
                break
            if type_snippet in all_defined_classes[parent][0]:
                full_type = type_snippet
                break

    if not full_type:
        type_snippet_prefix = type_snippet.split(".")[0]
        type_snippet_suffix = ".".join(type_snippet.split(".")[1:])
        for imported in imports:
            if ("." + imported).endswith("." + type_snippet_prefix):
                full_type = imported + (type_snippet_suffix and "." + type_snippet_suffix or "")
                break

    if not full_type:
        for default_type in all_default_classes:
            if ("." + default_type).endswith("." + type_snippet):
                full_type = default_type
                break

    if not full_type:
        full_class_name_chunks = class_full_name.split(".")
        for cut in xrange(len(full_class_name_chunks), -1, -1):
            hypo = ".".join(full_class_name_chunks[:cut]) + "." + type_snippet
            if hypo in all_defined_classes:
                full_type = hypo
                break

    if not full_type:
        if package_name + "." + type_snippet in all_defined_classes:
            full_type = package_name + "." + type_snippet
    if not full_type:
        hypos = defined_classes_by_suffix.get("." + type_snippet, [])
        hypos = [hypo for hypo in hypos if hypo.startswith(package_name + ".")]
        if len(hypos) == 1:
            full_type = hypos[0]
    if not full_type and not hypos:
        hypos = defined_classes_by_suffix.get("." + type_snippet, [])
        if len(hypos) == 1:
            full_type = hypos[0]
    # if not full_type:
    #    print type_snippet, package_name, [class_full_name], hypos
    return full_type


def get_full_type(type_node, source,
            package_name, class_full_name,
            class_methods_type_params,
            visible_classes,
            external_imports,
            all_defined_classes, defined_classes_by_prefix, defined_classes_by_suffix):
    # TODO: add visibility from the inherited classes
    type_snippet = type_node.get_snippet(source)
    type_snippet = type_snippet.split("<")[0] \
        .replace("[]", "") \
        .replace("\n", "").replace("\t", "") \
        .replace(" ", "").strip()

    full_type = None
    if not full_type:
        for method_node, method_param_types in class_methods_type_params:
            if method_node.start < type_node.start and method_node.end > type_node.end and type_snippet in method_param_types:
                full_type = type_snippet
                break
    # parents type params
    if not full_type:
        full_class_name_chunks = class_full_name.split(".")
        for cut in xrange(len(full_class_name_chunks), -1, -1):
            parent = ".".join(full_class_name_chunks[:cut])
            if not parent in all_defined_classes:
                break
            if type_snippet in all_defined_classes[parent][0]:
                full_type = type_snippet
                break
    if not full_type:
        type_snippet_prefix = type_snippet.split(".")[0]
        type_snippet_suffix = ".".join(type_snippet.split(".")[1:])
        for imported in visible_classes:
            if ("." + imported).endswith("." + type_snippet_prefix):
                full_type = imported + (type_snippet_suffix and "." + type_snippet_suffix or "")
                break
    if not full_type:
        type_snippet_prefix = type_snippet.split(".")[0]
        type_snippet_suffix = ".".join(type_snippet.split(".")[1:])
        for imported in external_imports:
            if ("." + imported).endswith("." + type_snippet_prefix):
                full_type = imported + (type_snippet_suffix and "." + type_snippet_suffix or "")
                break
    if not full_type:
        for default_type in all_default_classes:
            if ("." + default_type).endswith("." + type_snippet):
                full_type = default_type
                break
    if not full_type:
        full_class_name_chunks = class_full_name.split(".")
        for cut in xrange(len(full_class_name_chunks), -1, -1):
            hypo = ".".join(full_class_name_chunks[:cut]) + "." + type_snippet
            if hypo in all_defined_classes:
                full_type = hypo
                break
    if not full_type:
        if package_name + "." + type_snippet in all_defined_classes:
            full_type = package_name + "." + type_snippet

    if not full_type:
        hypos = defined_classes_by_suffix.get("." + type_snippet, [])
        hypos = [hypo for hypo in hypos if hypo.startswith(package_name + ".")]
        if len(hypos) == 1:
            full_type = hypos[0]

    if not full_type and not hypos:
        hypos = defined_classes_by_suffix.get("." + type_snippet, [])
        if len(hypos) == 1:
            full_type = hypos[0]
    return full_type


def infer_types_of_class_properties(fname, nodes, all_packages, all_names, all_public_vars, all_methods,
                                    all_classes_decls, defined_classes_by_prefix, defined_classes_by_suffix):
    source = open(fname).read()

    classes = []
    for node in all_nodes(nodes):
        if node.labels & CLASS_LABELS:
            classes += [node]
    package_name = get_package(source, nodes)
    if not package_name:
        return
    imports = get_imports(source, nodes)

    visible_classes = []
    external_imports = []

    for imported in imports:
        imported = imported.replace(".*", "").strip()
        package_is_defined = False
        for other_package_name in all_packages:
            if other_package_name and imported.startswith(other_package_name):
                package_is_defined = True
                break
        if not package_is_defined:
            external_imports.append(imported)
            continue
        name = imported.split(".")[-1]
        if not name in all_names:
            external_imports.append(imported)
            continue
        matched = False
        if imported in all_public_vars:
            matched = True
        if imported in all_methods:
            matched = True
        if not matched:
            visible_classes_add = defined_classes_by_prefix.get(imported + ".", [])
            visible_classes += visible_classes_add
            if visible_classes_add:
                matched = True
        if not matched:
            external_imports.append(imported)

    classes = []
    for node in all_nodes(nodes):
        if node.labels & CLASS_LABELS:
            classes += [node]

    for class_node in classes:
        class_name, type_parameters_parsed, extends_parsed_strs = parse_class_declaration(class_node, source)
        parents = [other_class_node for other_class_node in classes \
                   if other_class_node.start < class_node.start and other_class_node.end >= class_node.end]
        parents = sorted(parents, key=lambda class_node: class_node.start)
        full_name = [package_name] + [parse_class_declaration(parent, source)[0].get_snippet(source) for parent in
                                      parents] + \
                    [class_name.get_snippet(source)]
        full_name = ".".join(full_name)
        variables = find_all_var_declarations(class_node, source)
        for var_name, type_node, value_node, var_scope in variables:
            if var_scope == class_node:
                var_full_path = full_name + "." + var_name.get_snippet(source)
                full_type = type_node and get_full_type(type_node, source,
                              package_name, full_name,
                              [],
                              visible_classes,
                              external_imports,
                              all_classes_decls, defined_classes_by_prefix, defined_classes_by_suffix)
                #if not full_type and type_node:
                #    print "ASDASDFDF", [var_name.get_snippet(source)], fname
                all_public_vars[var_full_path] = (var_name, type_node, full_type, value_node, fname)







def infer_types_of_vars_impl(fname, nodes, all_packages, all_names, all_public_vars,
                             all_methods, method_name2full_names, class2parents,
                             all_classes_decls, defined_classes_by_prefix, defined_classes_by_suffix,
                             full_type_markup, stat):
    source = open(fname).read()
    classes = []
    for node in all_nodes(nodes):
        if node.labels & CLASS_LABELS:
            classes += [node]
    package_name = get_package(source, nodes)
    if not package_name:
        return
    imports = get_imports(source, nodes)
    visible_classes = []
    visible_vars = []
    visible_methods = []
    external_imports = []
    for imported in imports:
        imported = imported.replace(".*", "").strip()
        package_is_defined = False
        for other_package_name in all_packages:
            if other_package_name and imported.startswith(other_package_name):
                package_is_defined = True
                break
        if not package_is_defined:
            external_imports.append(imported)
            continue
        name = imported.split(".")[-1]
        if not name in all_names:
            external_imports.append(imported)
            continue
        matched = False
        if imported in all_public_vars:
            visible_vars += [imported]
            matched = True
        if imported in all_methods:
            visible_methods += [imported]
            matched = True
        if not matched:
            if imported + "." in defined_classes_by_prefix:
                visible_classes += defined_classes_by_prefix[imported + "."]
                matched = True
        if not matched:
            external_imports.append(imported)

    for class_node in classes:
        class_name, type_parameters_parsed, extends_parsed_strs = parse_class_declaration(class_node, source)
        parents = [other_class_node for other_class_node in classes \
                   if other_class_node.start < class_node.start and other_class_node.end >= class_node.end]
        parents = sorted(parents, key=lambda class_node: class_node.start)
        class_full_name = [package_name] + [parse_class_declaration(parent, source)[0].get_snippet(source) for parent in
                                            parents] + \
                          [class_name.get_snippet(source)]
        class_full_name = ".".join(class_full_name)

        class_methods_type_params = []
        for node in class_node.children:
            if METHOD_DECL_LABELS & node.labels:
                return_type, method_name, params, output_type_params = parse_method_declaration(class_node, node, source)
                # method_full_name = class_full_name + "." + method_name.get_snippet(source)
                param_type_names = []
                for elem in output_type_params:
                    method_param_node = elem
                    while method_param_node.children:
                        method_param_node = method_param_node.children[0]
                    param_type_names.append(method_param_node.get_snippet(source))
                    # print method_param_node.get_snippet(source)
                    class_methods_type_params.append((node, set(param_type_names)))

        variables = find_all_var_declarations(class_node, source)
        vars_full_types = []
        by_local_vname = {}
        for var_name, type_node, value_node, scope in variables:
            if not type_node:
                continue
            full_type = get_full_type(type_node, source,
                                      package_name, class_full_name,
                                      class_methods_type_params,
                                      visible_classes,
                                      external_imports,
                                      all_classes_decls, defined_classes_by_prefix, defined_classes_by_suffix)
            var_name_snippet = var_name.get_snippet(source).replace("[]", "").strip()
            vars_full_types.append((var_name_snippet, full_type, scope))
            full_type_markup[(fname, var_name.start, var_name.end)] = (full_type, (fname, var_name.start, var_name.end))
            by_local_vname.setdefault(var_name_snippet, []).append((full_type, var_name, type_node, value_node, scope))

        simple_names_in_class = []
        def collect_simple_names(stack):
            if stack[-1] != class_node and stack[-1].labels & CLASS_LABELS: #do not go into subclusses
                return False
            if stack[-1].labels & set(["expr.SimpleName", "expr.NameExpr"]):
                simple_names_in_class.append(stack[-1])
            return True


        class_node.DFS1([], collect_simple_names)
        #if visible_vars:
        #    print visible_vars
        for node in simple_names_in_class:
            node_snippet = node.get_snippet(source)
            if node_snippet in ["this", "super"]:
                continue
            full_type = get_full_type(node, source,
                                      package_name, class_full_name,
                                      class_methods_type_params,
                                      visible_classes,
                                      external_imports,
                                      all_classes_decls, defined_classes_by_prefix, defined_classes_by_suffix)
            if full_type:
                full_type_markup[(fname, node.start, node.end)] = (full_type, "")
                continue
            # check local
            matched = False
            if node_snippet in by_local_vname:
                for full_type, var_name, type_node, value_node, scope in by_local_vname[node_snippet]:
                    if scope.start <= node.start and scope.end >= node.end:
                        matched = True
                        full_type_markup[(fname, node.start, node.end)] = (full_type, (fname, var_name.start, var_name.end))
                        break
            if matched:
                continue

            # check parents variables:
            scopes2check = []
            class_full_name_chunks = class_full_name.split(".")
            for cut in xrange(len(class_full_name_chunks), -1, -1):
                current_class_full_name = ".".join(class_full_name_chunks[:cut])
                if not current_class_full_name in all_classes_decls:
                    break
                last_len = len(scopes2check)
                scopes2check.append(current_class_full_name)
                while last_len < len(scopes2check):
                    new_chunk = []
                    for scope_full_name in scopes2check[last_len:]:
                        if scope_full_name in class2parents:
                            new_chunk += class2parents[scope_full_name]
                    last_len = len(scopes2check)
                    scopes2check += list(set(new_chunk) - set(scopes2check))
            # print class_full_name, scopes2check, fname
            for scope_full_name in scopes2check:
                hypo_full_var_name = scope_full_name + "." + node_snippet
                if hypo_full_var_name in all_public_vars:
                    linked_var_name, linked_type_node, linked_full_type_str, linked_value_node, linked_fname = \
                    all_public_vars[hypo_full_var_name]
                    full_type_markup[(fname, node.start, node.end)] = (
                    linked_full_type_str, (linked_fname, linked_var_name.start, linked_var_name.end))
                    matched = True
                    break
            if matched:
                continue
            for full_var_name in visible_vars:
                if full_var_name.endswith("." + node_snippet):
                    matched = True
                    #print "full name:", full_var_name
                    linked_var_name, linked_type_node, linked_full_type_str, linked_value_node, linked_fname = \
                    all_public_vars[full_var_name]
                    full_type_markup[(fname, node.start, node.end)] = (
                    linked_full_type_str, (linked_fname, linked_var_name.start, linked_var_name.end))
                    break

        class_method_calls = []


        def find_method_calls(stack):
            node = stack[-1]
            if is_class_def(node) and class_node != node:
                return False
            if "expr.MethodCallExpr" in node.labels:
                class_method_calls.append(node)
            return True


        class_node.DFS1([], find_method_calls)

        for method_call in class_method_calls:
            try:
              caller_node, method_name_node, method_type_values_nodes, param_nodes = decompose_method_call(method_call,
                                                                                                         source)
            except:
              raise Exception("parse error",  "can't parse method call: " + method_call.get_snippet(source).replace("\n", " ") + "\nfname:" + fname)
              exit(1)
            method_name = method_name_node.get_snippet(source)
            stat[0] += 1
            hypos = method_name in method_name2full_names and method_name2full_names[method_name] or []
            if 1:
                filtered = []
                for possible_method in hypos:
                    params_count = all_methods[possible_method][0]
                    if params_count == len(param_nodes):
                        filtered.append(possible_method)
                hypos = filtered
            if not hypos:
                continue
            stat[1] += 1

            caller_snippet = caller_node and caller_node.get_snippet(source) or ""
            caller_snippet = caller_snippet.split("[")[0].strip()
            layer = set()
            parents = []
            if caller_snippet in ["", "this"]:
                layer = set([class_full_name])
            elif caller_snippet == "super":
                if class_full_name in class2parents:
                    layer = set(class2parents[class_full_name])
            else:
                # assume type name
                possible_full_type = get_full_type(caller_node, source,
                                                   package_name, class_full_name,
                                                   class_methods_type_params,
                                                   visible_classes,
                                                   external_imports,
                                                   all_classes_decls, defined_classes_by_prefix, defined_classes_by_suffix)
                if possible_full_type:
                    layer = set([possible_full_type])

                # check local variables
                if not layer:
                    for var_name_snippet, var_name_full_type, var_scope in vars_full_types:
                        if var_name_snippet == caller_snippet and var_scope.start <= method_call.start and var_scope.end >= method_call.end:
                            layer = set([var_name_full_type])
                            break

                # check parents variables:
                if not layer:
                    parents = []
                    class_full_name_chunks = class_full_name.split(".")
                    for cut in xrange(len(class_full_name_chunks), -1, -1):
                        current_class_full_name = ".".join(class_full_name_chunks[:cut])
                        if not current_class_full_name in all_classes_decls:
                            break
                        last_len = len(parents)
                        parents.append(current_class_full_name)
                        while last_len < len(parents):
                            new_chunk = []
                            for parent in parents[last_len:]:
                                if parent in class2parents:
                                    new_chunk += class2parents[parent]
                            last_len = len(parents)
                            parents += list(set(new_chunk) - set(parents))

                    for parent in parents:
                        if not parent:
                            continue
                        hypo_full_var_name = parent + "." + caller_snippet
                        if hypo_full_var_name in all_public_vars:
                            if not all_public_vars[hypo_full_var_name][2]:
                                continue
                            public_var_type_short = all_public_vars[hypo_full_var_name][2].split("[")[0].split("<")[
                                0].replace(" ", "").strip()
                            layer = set([hypo for hypo in all_default_classes if
                                         ("." + hypo).endswith("." + public_var_type_short)])
                            if not layer:
                                layer = set(defined_classes_by_suffix.get("." + public_var_type_short, []))
                            break
                if 0:
                    if not layer:
                        print [caller_snippet], [vns for vns, _, _ in vars_full_types]
                        for var_name_snippet, var_name_full_type, var_scope in vars_full_types:
                            print "\t\t", var_scope.labels
                            print "\t", var_name_snippet, var_name_full_type, [
                                var_scope.get_snippet(source).replace("\n", " ")[:100]]
                        print fname
                        print "---"
            used = set()
            matched = False
            initial_layer = [item for item in layer]
            while layer and not matched:
                used = used | set(layer)
                next_layer = []
                for hypo_root in layer:
                    if not hypo_root:
                        continue
                    if hypo_root in class2parents:
                        next_layer += class2parents[hypo_root]
                    minus_last_chunk = ".".join(hypo_root.split(".")[:-1])
                    if minus_last_chunk in all_classes_decls:
                        next_layer += [minus_last_chunk]
                    full_method_name = hypo_root + "." + method_name
                    if full_method_name in hypos:
                        hypos = [full_method_name]
                        matched = True
                        break
                layer = set(next_layer) - used

            if matched:
                full_method_name = hypos[0]
                full_type_markup[(fname, method_call.start, method_call.end)] = full_method_name
                full_type_markup[(fname, method_name_node.start, method_name_node.end)] = full_method_name
                stat[2] += 1

            if 0:
                if not matched:
                    print [caller_snippet], method_name, initial_layer
                    print "\t", full_method_name, hypos
                    print "\t", class_full_name
                    print "\t", parents
                    print "\t", fname

                    # for node in simple_names_in_class:
                    #    if not (fname, node.start, node.end) in full_type_markup:
                    #        print "ASDASD", [node.get_snippet(source)], fname
