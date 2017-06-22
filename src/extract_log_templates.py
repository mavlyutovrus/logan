from utils import *
import pickle
import os
import shelve
from find_var_defs import find_all_var_declarations

THIS = 3224232434
MAX_NUMBER_OF_CHAINS_PER_LOGLINE = 10000

class LogExtractor(object):
    def __init__(self, index_folder, output_loc):
        self.index_folder = index_folder
        (self.all_names, self.all_packages, self.all_classes_decls,
               self.all_methods, self.all_public_vars, self.class2parents, self.full_type_markup) = \
                                pickle.load(open(os.path.join(index_folder, "source_index.b"), "rb"))

        markup_db_loc = os.path.join(index_folder, "markup.db")
        self.markup_db = shelve.open(markup_db_loc, flag='r')

        self.full_method_name2calls = {}
        for (fname, call_start, call_end), full_method_name in self.full_type_markup.items():
            if not isinstance(full_method_name, tuple):
                self.full_method_name2calls.setdefault(full_method_name, []).append((fname, call_start, call_end))

        self.method_name2full_names = {}
        for method_full_name in self.all_methods.keys():
            method_name = method_full_name.split(".")[-1]
            self.method_name2full_names.setdefault(method_name, []).append(method_full_name)

        self.fname2classes = {}
        for class_full_name, (type_param_names, package_name, imports, extends_parsed_strs,
                                            (class_start, class_end, fname))  in self.all_classes_decls.items():
            self.fname2classes.setdefault(fname, []).append(class_full_name)
        self.stack_of_expansions = []

        self.logging = sys.stderr #open("logging.txt", "w")
        self.output = output_loc == "-" and sys.stdout or open(output_loc, "w")
        self.extracted_log_templates = []
        processed = 0

        #fname = "/home/arslan/src/provenance/hadoop/hadoop-hdfs-project/hadoop-hdfs/src/main/java/org/apache/hadoop/hdfs/server/datanode/BlockReceiver.java"
        #root_node_str = self.markup_db[fname]
        #if 1:
      
        self.logging.write("Total sources " + str(len(self.markup_db)) + "\n")
        for fname, root_node_str in self.markup_db.items():
            processed += 1
            if processed % 100 == 0:
                self.logging.write("..processed " + str(processed) + "\n")
                self.logging.flush()
            root_node = FromString2Node(root_node_str)
            self.extract_log_lines(fname, root_node)
            self.output.flush()
        self.logging.close()
        self.output.flush()


    def extract_log_calls_from_method_declartion(self, method_decl_node, source):
        log_call_stacks = []
        def get_log_call_stacks(node_stack):
            node = node_stack[-1]
            if "expr.MethodCallExpr" in node.labels:
                method_call_text = node.get_snippet(source).lower()
                pre_call_snippet = method_call_text.split("(")[0].strip()
                if "log" in pre_call_snippet and \
                       ("info" in pre_call_snippet or "warn" in pre_call_snippet or "debug" in pre_call_snippet) or \
                         "logauditmessage" in pre_call_snippet:
                    log_call_stacks.append([item for item in node_stack])
                    return False
            return True
        method_decl_node.DFS1([], get_log_call_stacks)
        return log_call_stacks

    def get_method_call_params_chains_safe(self, node, source):
        method_names_and_params = []
        caller = node
        while caller:
            caller, method_name_node, method_type_values_nodes, param_nodes = decompose_method_call(caller, source)
            if method_name_node:
                method_names_and_params = [(method_name_node.get_snippet(source),[[param] for param in param_nodes])] + method_names_and_params
        return method_names_and_params

    def check_if_constant(self, var_node, source, fname):
        key = (fname, var_node.start, var_node.end)
        if not key in self.full_type_markup:
            return []
        try:
            full_type, origin = self.full_type_markup[key]
            orig_fname, orig_start, orig_end = origin
        except:
            return []
        orig_file_tree =  FromString2Node(self.markup_db[orig_fname])
        origin_node = [node for node in all_nodes(orig_file_tree) if node.start == orig_start and node.end == orig_end][0]
        origin_class_full_name = ""
        class_start, class_end = -1, -1
        for cur_class_full_name in self.fname2classes[orig_fname]:
            cur_class_start, cur_class_end, _ = self.all_classes_decls[cur_class_full_name][-1]
            if cur_class_start <= origin_node.start and cur_class_end >= origin_node.end \
                    and len(cur_class_full_name) > len(origin_class_full_name):
                origin_class_full_name = cur_class_full_name
                class_start, class_end = cur_class_start, cur_class_end
        full_name = origin_class_full_name + "." + origin_node.get_snippet(open(orig_fname, "r").read())
        if full_name in self.all_public_vars:
            value_node = self.all_public_vars[full_name][-2]
            if value_node:
                orig_class_node = [node for node in all_nodes(orig_file_tree) if
                                   node.start == class_start and node.end == class_end]
                origin_source = open(orig_fname).read()
                #print "[VARIABLE]", full_name, [value_node.get_snippet(origin_source)]
                return [(orig_fname, origin_class_full_name, orig_class_node, origin_source, value_node)]
        return []

    def get_assigments(self, var_node, method_node, source, fname):
        var_name = var_node.get_snippet(source).split("[")[0]
        key = (fname, var_node.start, var_node.end)
        try:
            full_type, origin = self.full_type_markup[key]
            orig_fname, orig_start, orig_end = origin
        except:
            #print "getting type miss", var_node.get_snippet(source), var_node.labels, [fname]
            return []

        origin_node = None
        origin_value = None
        origin_expression = None
        if orig_fname == fname and orig_start > method_node.start and orig_end < method_node.end:
            origin_node = [node for node in all_nodes(method_node) if node.start == orig_start and node.end == orig_end][0]
            origin_value = \
                       [cur_value_node for cur_var_name, _, cur_value_node, _ in find_all_var_declarations(method_node, source, go_in_classes=True)
                               if cur_var_name.start == origin_node.start and cur_var_name.end == origin_node.end][0]
            if origin_value:
                origin_expression = build_path(origin_value, method_node)[-2]

        node_usage = []
        for node in all_nodes(method_node):
            node_snippet = node.get_snippet(source).split("[")[0]
            if node_snippet == var_name and (not origin_node or node.start >= origin_node.end) and node.end < var_node.start:
                node_usage.append(node)
        node_assignements = []
        used = set()
        for node in node_usage:
            statement = None
            for path_node in reversed(build_path(node, method_node)):
                if is_statement(path_node):
                    statement = path_node
                    break
            if not statement:
                continue
            if not 'stmt.ExpressionStmt' in statement.labels:
                continue
            if len(statement.children) != 1 or not 'expr.AssignExpr' in statement.children[0].labels:
                continue
            expression = statement.children[0]
            assigned_to = expression.children[0].get_snippet(source).split("[")[0]
            pos_key = (expression.start, expression.end)
            if assigned_to == var_name and not pos_key in used:
                node_assignements.append((expression.children[1], statement))
                used.add(pos_key)
        if origin_value:
            node_assignements.append((origin_value, origin_expression))

        #do not expand recuirsive assignements
        for assignement, expression in node_assignements:
            for node in all_nodes(assignement):
                has_loop = node.get_snippet(source) == var_name and source[node.start - 1] != "."
                if has_loop:
                    #print "\t\tLOOP", [var_name], [expression.get_snippet(source)]
                    return []

        variable_assignement_nodes = sorted(node_assignements, key=lambda pair: pair[0].end)

        branches_keys = set()
        branches = []
        var_modifications = []
        for node_index in xrange(len(variable_assignement_nodes)):
            node, expression = variable_assignement_nodes[node_index]
            path2var_node = build_path(node, method_node)
            cond_path = []
            cond_path_str = ""
            for path_pos in xrange(len(path2var_node) - 1):
                path_node = path2var_node[path_pos]
                next_path_node = path2var_node[path_pos + 1]
                if 'stmt.IfStmt' in path_node.labels:
                    child_index = \
                    [index for index in xrange(len(path_node.children)) if path_node.children[index] == next_path_node][0]
                    cond_path += [(path_node.start, path_node.end, child_index)]
                    cond_path_str += str(path_node.start) + ":" + str(path_node.end) + ":" + str(child_index) + "_"
            var_modifications += [(cond_path_str, node, expression)]
            if cond_path and not (cond_path_str in branches_keys):
                branches.append(cond_path)
                branches_keys.add(cond_path_str)

        final_chains = []
        # print branches
        for comb in xrange(2 ** len(branches)):
            taken_branches = []
            not_taken_branches = []
            ifs = {}
            for branch in branches:
                take = comb % 2
                comb >>= 1
                if take:
                    taken_branches.append(branch)
                    for ifstart, ifend, branch_index in branch:
                        ifs.setdefault((ifstart, ifend), set()).add(branch_index)
                else:
                    not_taken_branches.append(branch)
            controversial = False
            for if_key, taken_branches_indices in ifs.items():
                if len(taken_branches_indices) != 1:
                    controversial = True
                    break
            if not controversial:
                taken_ifs_selection = []
                for taken_branch in taken_branches:
                    taken_ifs_selection += taken_branch
                for not_taken_branch in not_taken_branches:
                    if not_taken_branch[-1] in taken_ifs_selection:
                        controversial = True
                        break
            if controversial:
                continue
            taken_branches_keys = set(["".join([str(ifstart) + ":" + str(ifend) + ":" + str(if_ch_index) + "_" \
                                                for ifstart, ifend, if_ch_index in branch]) for branch in taken_branches])
            chain = []
            for branch_key, node, expression in var_modifications:
                if not branch_key or branch_key in taken_branches_keys:
                    chain.append(node)
                    marker = origin_node and origin_node.start < expression.end and origin_node.end > expression.start and "*" or ""
                    #print "\t\t\t", marker, (expression.start, expression.end), expression.get_snippet(source)
            if chain:
                final_chains.append(chain)
                #print "---"
        return final_chains

    def get_variable_provenance(self, var_node, method_node, source, fname, class_full_name, class_node):
        var_name = var_node.get_snippet(source).split("[")[0]
        key = (fname, var_node.start, var_node.end)
        if not key in self.full_type_markup:
            return []
        if not isinstance(self.full_type_markup[key], tuple):
            return []
        full_type, origin = self.full_type_markup[key]
        if not full_type in primitive_types and not full_type in ["String"]:
            return []
        orig_fname, orig_start, orig_end = origin
        if orig_fname != fname or orig_start < method_node.start or orig_end > method_node.end:
            return []
        origin_node = [node for node in all_nodes(method_node) if node.start == orig_start and node.end == orig_end][0]
        #origin_value = [cur_value_node for cur_var_name, _, cur_value_node, _ in find_all_var_declarations(method_node, source)
        #                            if cur_var_name.start == origin_node.start and cur_var_name.end == origin_node.end][0]

        #if params propagate to parent methods
        _, method_name_node, params, _ = parse_method_declaration(class_node, method_node, source)
        matched_param_index = -1
        #print method_node.get_snippet(source).replace("\n", " ")[:300], ".."
        #print "var_name:", var_name.get_snippet(source)
        param_count = len(params)
        for param_index in xrange(len(params)):
            param_name = params[param_index][0]
            if param_name.start <= origin_node.start and param_name.end >= origin_node.end:
                matched_param_index = param_index
                #print "param:", param_name.get_snippet(source)
        if matched_param_index == -1:
            return []
        method_full_name = class_full_name + "." + method_name_node.get_snippet(source)
        #print "\t\t[PARAM]", [var_node.get_snippet(source)], method_node.get_snippet(source).replace("\n", " ")[:300]
        callers = []
        if matched_param_index > -1 and method_full_name in self.full_method_name2calls:
            #print " " * offset, 'orig fname:', fname
            #print " " * offset, "orig class:", class_full_name
            #print " " * offset, "[METHOD]", method_full_name, "param index:", matched_param_index
            #print " " * offset, "var:", var_name, "type:", full_type
            for caller_fname, caller_node_start, caller_node_end in self.full_method_name2calls[method_full_name]:
                caller_source = open(caller_fname).read()
                caller_file_tree =  FromString2Node(self.markup_db[caller_fname])
                caller_method_node = None
                for node in all_nodes(caller_file_tree):
                    if node.start == caller_node_start and node.end == caller_node_end:
                        caller_method_node = node
                        break
                if not 'expr.MethodCallExpr' in caller_method_node.labels:
                    continue

                _, _, _, param_nodes = decompose_method_call(caller_method_node, caller_source)
                if len(param_nodes) != param_count:
                    continue
                #get related class
                caller_class_node = None
                caller_class_full_name = ""

                for cur_class_full_name in self.fname2classes[caller_fname]:
                    cur_class_start, cur_class_end, _ = self.all_classes_decls[cur_class_full_name][-1]
                    if cur_class_start <= caller_method_node.start and cur_class_end >= caller_method_node.end \
                                    and len(cur_class_full_name) > len(caller_class_full_name):
                        caller_class_full_name = cur_class_full_name
                if not caller_class_full_name:
                    continue
                caller_class_start, caller_class_end, _ = self.all_classes_decls[caller_class_full_name][-1]
                caller_class_node = [node for node in all_nodes(caller_file_tree) if node.start == caller_class_start and node.end == caller_class_end][0]

                caller_cont_method_node = [node for node in reversed(build_path(caller_method_node, caller_class_node)) \
                                           if node.labels & set(["body.MethodDeclaration", "body.ConstructorDeclaration"])]

                if not caller_cont_method_node:
                    continue
                caller_cont_method_node = caller_cont_method_node[0]
                caller_cont_method_node_name = parse_method_declaration(caller_class_node, caller_cont_method_node,
                                                                        caller_source)[1].get_snippet(caller_source)
                #print "\tcaller fname:", caller_fname
                #print "\tcaller class:", caller_class_full_name
                #print "\tcall:", caller_method_node.get_snippet(caller_source).replace("\n", " ")
                #print "\ttarget_param_value:", param_nodes[matched_param_index].get_snippet(caller_source)
                #print "\tcaller_containing_method:", caller_cont_method_node_name
                #print "---"
                callers.append((caller_source, caller_fname, caller_class_full_name, caller_class_node, caller_cont_method_node, param_nodes[matched_param_index]))
        return callers

    def expand_string_var(self, string_var_node, root_node, source):
        path2var_node = build_path(string_var_node, root_node)
        method_node = None
        for node_in_path in path2var_node:
            if node_in_path.labels & set(["body.MethodDeclaration", 'body.ConstructorDeclaration']):
                method_node = node_in_path
        variable_assignement_nodes = []
        other_occurences = []
        obj_snippet = string_var_node.get_snippet(source)
        def find_variable_updates(stack):
            leaf = stack[-1]
            if leaf.start >= string_var_node.start:
                return False
            if leaf.get_snippet(source) == obj_snippet:
                used = False
                for node in stack:
                    if ("body.VariableDeclarator" in node.labels or "expr.AssignExpr" in node.labels) and node.children:
                        if node.end < string_var_node.start:
                            first_child = node.children[0]
                            while first_child.children:
                                first_child = first_child.children[0]
                            if first_child.get_snippet(source) == obj_snippet:
                                variable_assignement_nodes.append(node)
                                used = True
                if not used:
                    other_occurences.append( (stack[-3].get_snippet(source), [node.labels for node in stack[1:]], ) )
            return True
        method_node.DFS1([], find_variable_updates)
        return [assignement.children[1:] for assignement in variable_assignement_nodes]

    def expand_stringbuilder_var(self, stringbuilder_var_node, root_node, source):
        path2var_node = build_path(stringbuilder_var_node, root_node)
        method_node = None
        for node_in_path in path2var_node:
            if node_in_path.labels & set(["body.MethodDeclaration", 'body.ConstructorDeclaration']):
                method_node = node_in_path
        variable_assignement_nodes = []
        obj_snippet = stringbuilder_var_node.get_snippet(source)
        var_declaration_nodes = []
        #print obj_snippet
        used_spaces = set()
        def find_variable_updates(stack):
            leaf = stack[-1]
            if leaf.start >= stringbuilder_var_node.start:
                return False
            if leaf.get_snippet(source) == obj_snippet:
                for node in stack:
                    considered = False
                    for position in xrange(node.start, node.end):
                        if position in used_spaces:
                            considered = True
                            break
                    if considered:
                        continue
                    if "body.VariableDeclarator" in node.labels and node.children:
                        declare_snippet = node.get_snippet(source).replace("\n", " ")
                        #print "VARDECL", declare_snippet
                        if "StringBuilder(" in declare_snippet:
                            var_declaration_nodes.append(node)
                            constitutes = []
                            methods_and_params = self.get_method_call_params_chains_safe(node, source)
                            for method_name, params in methods_and_params:
                                if "StringBuilder" in method_name:
                                    if len(params) != 1 or not params[0] or not "expr.IntegerLiteralExpr" in params[0][0].labels:
                                        for param_nodes in params:
                                            constitutes += param_nodes
                                elif "append" in method_name:
                                    for param_nodes in params:
                                        constitutes += param_nodes
                                else:
                                    pass
                                    #print method_name
                        else:
                            constitutes = node.children[1:]
                            #print "CHEEECK:", [elem.get_snippet(source).replace("\n", " ") for elem in constitutes]
                        #for constitute in constitutes:
                        #    print "\t\t-> ", constitute.get_snippet(source)
                        for constitute in constitutes:
                            variable_assignement_nodes.append(constitute)
                        for position in xrange(node.start, node.end):
                            used_spaces.add(position)
                    if "expr.AssignExpr" in node.labels and node.children:
                        #print "ASSIGN", node.get_snippet(source).replace("\n", " ")
                        pass
                    if "expr.MethodCallExpr" in node.labels and node.children:
                        node_snippet = node.get_snippet(source).replace("\n", " ")
                        if node_snippet.startswith(obj_snippet):
                            #print "MethodCall", node_snippet
                            constitutes = []
                            methods_and_params = self.get_method_call_params_chains_safe(node, source)
                            for method_name, params in methods_and_params:
                                if "StringBuilder" in method_name or "append" in method_name:
                                    for param_nodes in params:
                                        constitutes += param_nodes
                                else:
                                    #raise Exception()
                                    pass
                            for constitute in constitutes:
                                variable_assignement_nodes.append(constitute)
                            for position in xrange(node.start, node.end):
                                used_spaces.add(position)
            return True
        method_node.DFS1([], find_variable_updates)

        variable_assignement_nodes = sorted(variable_assignement_nodes, key= lambda node : node.end)
        if var_declaration_nodes:
            min_node_start = max([node.start for node in  var_declaration_nodes])
            variable_assignement_nodes = [node for node in variable_assignement_nodes if node.start >= min_node_start]
        #print "Selected nodes:"
        #for node in variable_assignement_nodes:
        #    print "selected:\t", node.get_snippet(source).replace("\n", " ")
        branches_keys = set()
        branches = []
        var_modifications = []
        for node_index in xrange(len(variable_assignement_nodes)):
            node = variable_assignement_nodes[node_index]
            path2var_node = build_path(node, root_node)
            cond_path = []
            cond_path_str = ""
            for path_pos in xrange(len(path2var_node) - 1):
                path_node = path2var_node[path_pos]
                next_path_node = path2var_node[path_pos + 1]
                if 'stmt.IfStmt' in path_node.labels:
                    child_index = [index for index in xrange(len(path_node.children)) if path_node.children[index] == next_path_node][0]
                    cond_path += [(path_node.start, path_node.end, child_index)]
                    cond_path_str += str(path_node.start) + ":" + str(path_node.end) + ":" + str(child_index) + "_"
            var_modifications += [(cond_path_str, node)]
            if cond_path and not (cond_path_str in branches_keys):
                branches.append(cond_path)
                branches_keys.add(cond_path_str)

        final_chains = []
        #print branches
        for comb in xrange(2 ** len(branches)):
            taken_branches = []
            not_taken_branches = []
            ifs = {}
            for branch in branches:
                take = comb % 2
                comb >>= 1
                if take:
                    taken_branches.append(branch)
                    for ifstart, ifend, branch_index in branch:
                        ifs.setdefault((ifstart, ifend), set()).add(branch_index)
                else:
                    not_taken_branches.append(branch)
            controversial = False
            for if_key, taken_branches_indices in ifs.items():
                if len(taken_branches_indices) != 1:
                    controversial = True
                    break
            if not controversial:
                taken_ifs_selection = []
                for taken_branch in taken_branches:
                    taken_ifs_selection += taken_branch
                for not_taken_branch in not_taken_branches:
                    if not_taken_branch[-1] in taken_ifs_selection:
                        controversial = True
                        break
            if controversial:
                continue
            taken_branches_keys = set(["".join([str(ifstart) + ":" + str(ifend) + ":" + str(if_ch_index) + "_" \
                                    for ifstart, ifend, if_ch_index in branch]) for branch in taken_branches])
            #print "--"
            chain = []
            for branch_key, node in var_modifications:
                if not branch_key or branch_key in taken_branches_keys:
                    chain.append(node)
                    #print "\t\t--> ", node.get_snippet(source).replace("\n", " ")
            if chain:
                final_chains.append(chain)
            #print "--"
        #print "-------"
        #print len(branches_keys), branches_keys, branches
        return final_chains

    def expand(self, node, source, get_var_type_func, root_node, fname, class_full_name, class_node):
        if type(node) != TNode:
            stack_key = (node, class_full_name, root_node and root_node.start or -1, root_node and root_node.end or -1)
        else:
            stack_key = (node.start, node.end, class_full_name, root_node and root_node.start or -1, root_node and root_node.end or -1)
        if stack_key in self.stack_of_expansions:
            return []
        if type(node) == str:
            return [[node]]
        if node == THIS:
            return [[(THIS, source, fname, class_full_name)]]
        if "expr.StringLiteralExpr" in node.labels:
            return [[node.get_snippet(source).strip()[1:-1].replace("\\\"", "\"").replace("\\n", "<BR>").replace("\\t", "<TAB>") ]]
        if "expr.CharLiteralExpr" in node.labels:
            return [[node.get_snippet(source).strip()[1:-1].replace("\\\"", "\"").replace("\\n", "<BR>").replace("\\t", "<TAB>") ]]

        #if "expr.IntegerLiteralExpr" in node.labels:
        #    return [[node.get_snippet(source)], []]
        #if "expr.DoubleLiteralExpr" in node.labels:
        #    return [[node.get_snippet(source)], []]
        #if "expr.BooleanLiteralExpr" in node.labels:
        #    return [[node.get_snippet(source)], []]
        #if "expr.NullLiteralExpr" in node.labels:
        #    return [["null"], []]

        if "expr.BinaryExpr" in node.labels or 'expr.EnclosedExpr' in node.labels:
            outputs = [[]]
            for subnode in node.children:
                suffixes = self.expand(subnode, source, get_var_type_func, root_node, fname, class_full_name, class_node)
                new_outputs = []
                for output in outputs:
                    for suffix in suffixes:
                        new_outputs += [output + suffix]
                outputs = new_outputs
            return outputs
        if "expr.ConditionalExpr" in node.labels and len(node.children) != 3:
            return self.expand(node.children[1], source, get_var_type_func, root_node, fname, class_full_name, class_node) + \
                   self.expand(node.children[2], source, get_var_type_func, root_node, fname, class_full_name, class_node)

        if "expr.ThisExpr" in node.labels:
            return [[(THIS, source, fname, class_full_name)]]

        if "expr.SimpleName" in node.labels or "expr.NameExpr" in node.labels:
            node_type = get_var_type_func(node, fname)
            """
            if node_type and ("." + node_type).endswith(".String"):
                possible_expansions = expand_string_var(node, root_node, source)
                all_chains = []
                for chain in possible_expansions:
                    all_chains += cortesian_sum([expand(chain_node, source, get_var_type_func, root_node, fname) for chain_node in chain])
                if all_chains:
                    return all_chains
            """

            if node_type and "StringBuilder" in node_type and root_node:
                #print "Started for:", node_type, "::", node.get_snippet(source)
                possible_expansions = self.expand_stringbuilder_var(node, root_node, source)
                all_chains = []
                for chain in possible_expansions:
                    #for node in chain:
                    #    print "-->\t", node.get_snippet(source)
                    #print "--"
                    all_chains += cortesian_sum([self.expand(chain_node, source, get_var_type_func, root_node,
                                                             fname, class_full_name, class_node) for chain_node in chain])
                if all_chains:
                    return all_chains

            #get all assignements
            if root_node:# and (node_type in primitive_types or node_type == "String"):
                #print "[VAR]", (node.start, node.end), node.get_snippet(source), node_type
                possible_expansions = self.get_assigments(node, root_node, source, fname)
                all_chains = []
                for chain in possible_expansions:
                    all_chains += cortesian_sum([self.expand(chain_node, source, get_var_type_func, root_node,
                                                        fname, class_full_name, class_node) for chain_node in chain])
                if all_chains:
                    return all_chains

            #class fields
            for orig_fname, orig_class_full_name, orig_class_node, orig_source, value_node in self.check_if_constant(node, source, fname):
                #return [[(node, source, fname, class_full_name)]]
                return self.expand(value_node, orig_source, get_var_type_func, None, orig_fname, orig_class_full_name, orig_class_node)

            #if a method param, go to callers
            if root_node and len(self.stack_of_expansions) < 2:
                self.stack_of_expansions.append(stack_key)
                possible_callers = self.get_variable_provenance(node, root_node, source, fname, class_full_name, class_node)
                expansions = []
                for caller_source, caller_fname, caller_class_full_name, caller_class_node, caller_cont_method_node, caller_param_value in possible_callers:
                    expansions += self.expand(caller_param_value, caller_source, get_var_type_func,
                                              caller_cont_method_node, caller_fname, caller_class_full_name, caller_class_node)
                self.stack_of_expansions.pop()
                if expansions:
                    return expansions

            return [[(node, source, fname, class_full_name)]]

        if "expr.FieldAccessExpr" in node.labels:
            return [[(node, source, fname, class_full_name)]]

        if "expr.ArrayAccessExpr" in node.labels:
            return self.expand(node.children[0], source, get_var_type_func, root_node, fname, class_full_name, class_node)

        if "expr.UnaryExpr" in node.labels:
            return self.expand(node.children[0], source, get_var_type_func, root_node, fname, class_full_name, class_node)

        if "expr.MethodCallExpr" in node.labels:
            caller, method_name_node, _, params = decompose_method_call(node, source)
            method_name = method_name_node.get_snippet(source)
            if not params and method_name == "toString":
                return caller and self.expand(caller, source, get_var_type_func, root_node, fname, class_full_name, class_node) or [[(THIS, source, fname, class_full_name)]]
            if len(params) == 1 and not caller and method_name == "toString":
                return self.expand(params[0], source, get_var_type_func, root_node, fname, class_full_name, class_node)
            if method_name in ["stringify", "stringifyException"]:
                return self.expand(params[0], source, get_var_type_func, root_node, fname, class_full_name, class_node)
            if method_name in ["formatTime"] and caller and caller.get_snippet(source) == "StringUtils":
                return cortesian_sum([self.expand(param_node, source, get_var_type_func, root_node,
                                                fname, class_full_name, class_node) for param_node in params])

            if method_name in ["join"] and caller and caller.get_snippet(source) == "StringUtils":
                if params[1].labels & set(['expr.CharLiteralExpr', "expr.StringLiteralExpr"]):
                    return self.expand(params[0], source, get_var_type_func, root_node, fname, class_full_name, class_node)
                else:
                    return self.expand(params[1], source, get_var_type_func, root_node, fname, class_full_name, class_node)
            if method_name in ["byteDesc"] and caller and caller.get_snippet(source) == "StringUtils":
                return self.expand(params[0], source, get_var_type_func, root_node, fname, class_full_name, class_node)
            if method_name in ["toString", "asList"] and caller and caller.get_snippet(source) == "Arrays":
                return self.expand(params[0], source, get_var_type_func, root_node, fname, class_full_name, class_node)
            if caller and caller.get_snippet(source).startswith("Joiner"):
                return self.expand(params[0], source, get_var_type_func, root_node, fname, class_full_name, class_node)
            if caller and caller.get_snippet(source) == "TextFormat":
                return self.expand(params[0], source, get_var_type_func, root_node, fname, class_full_name, class_node)
            if method_name in ["mapToString"] and caller and caller.get_snippet(source) == "QuorumCall":
                return self.expand(params[0], source, get_var_type_func, root_node, fname, class_full_name, class_node)

            if caller and caller.get_snippet(source).startswith("MessageFormat") and method_name == "format":
                format_string = ""
                for subnode in all_nodes_post_order(params[0]):
                    if "expr.BinaryExpr" in subnode.labels:
                        continue
                    if not "expr.StringLiteralExpr" in subnode.labels:
                        #TODO: expand
                        raise Exception("MessageFromat expansion fails", "Expected string constant, got smth else: " + " ".join(subnode.labels))
                        return [[node]]
                    format_string += subnode.get_snippet(source).strip()[1:-1]
                by_pos = []
                keys = []
                for format_param_index in xrange(1, len(params)):
                    key = "{" + str(format_param_index - 1) + "}"
                    by_pos += [(format_string.find(key), format_param_index)]
                    keys.append(key)
                for key in keys:
                    format_string = format_string.replace(key, "{}")
                by_pos.sort()
                unrolled = [params[format_param_index] for _, format_param_index in by_pos]
                format_string_chunks = format_string.split("{}")
                for chunk_index in xrange(len(format_string_chunks) - 1, 0, -1):
                    unrolled = unrolled[:chunk_index] + [format_string_chunks[chunk_index]] + unrolled[chunk_index:]
                unrolled = [format_string_chunks[0]] + unrolled
                if 1:
                    outputs = [[]]
                    for subnode in unrolled:
                        suffixes = self.expand(subnode, source, get_var_type_func, root_node, fname, class_full_name, class_node)
                        new_outputs = []
                        for output in outputs:
                            for suffix in suffixes:
                                new_outputs += [output + suffix]
                        outputs = new_outputs
                    return outputs

            if caller and caller.get_snippet(source) == "String" and method_name == "format":
                format_string = ""
                format_string_assembled = False
                for chain in self.expand(params[0], source, get_var_type_func, root_node, fname, class_full_name, class_node):
                    if not [elem for elem in chain if not type(elem) == str]:
                        format_string = "".join(chain)
                        format_string_assembled = True
                        break
                if not format_string_assembled:
                    return [[(node, source, fname, class_full_name)]]
                import re
                keys = re.findall("%[0-9\.]*[a-z]", format_string)
                for key in keys:
                    format_string = format_string.replace(key, "{}")
                unrolled = params[1:]
                format_string_chunks = format_string.split("{}")
                for chunk_index in xrange(len(format_string_chunks) - 1, 0, -1):
                    unrolled = unrolled[:chunk_index] + [format_string_chunks[chunk_index]] + unrolled[chunk_index:]
                unrolled = [format_string_chunks[0]] + unrolled
                if 1:
                    outputs = [[]]
                    for subnode in unrolled:
                        suffixes = self.expand(subnode, source, get_var_type_func, root_node, fname, class_full_name, class_node)
                        new_outputs = []
                        for output in outputs:
                            for suffix in suffixes:
                                new_outputs += [output + suffix]
                        outputs = new_outputs
                    return outputs

        return [[(node, source, fname, class_full_name)]]
        #if "expr.EnclosedExpr" in node.labels:
        #    processing_deque = node.children + processing_deque
        #    continue
        #if "expr.ArrayAccessExpr" in node.labels:
        #    processing_deque = node.children + processing_deque
        #    continue
        #if "type.ClassOrInterfaceType" in node.labels:
        #    continue
        #if "type.PrimitiveType" in node.labels:
        #    continue
        #if "expr.ClassExpr" in node.labels:
        #    continue
        #if "expr." in node.labels:
        #    processing_deque = node.children + processing_deque
        #    # print node.get_snippet(source)
        #    continue
        #if "type.PrimitiveType" in node.labels:
        #    continue

    def get_log_line_constitutes(self, log_call_stack, source, fname, class_full_name, class_node, get_var_type_func):
        log_call_node = log_call_stack[-1]
        caller_node, method_name_node, method_type_values_nodes, parameters = decompose_method_call(log_call_node, source)
        #print log_call_node.get_snippet(source).replace("\n", " ")
        #print "---"
        if not parameters:
            return None
        expanded_params_chains = [self.expand(param, source, get_var_type_func, log_call_stack[0], fname, class_full_name, class_node) for param in parameters]

        unrolled_chains = [[item] for item in expanded_params_chains[0]]
        expanded_params_chains = expanded_params_chains[1:]
        while expanded_params_chains:
            next_chunk = expanded_params_chains[0]
            expanded_params_chains = expanded_params_chains[1:]
            new_all_chains = []
            for chain in unrolled_chains:
                for add_chain in next_chunk:
                    new_all_chains += [chain + [add_chain]]
            unrolled_chains = new_all_chains
        return unrolled_chains

    def extract_log_lines(self, fname, file_node):
        self.logging.write("[FILE] " + fname + "\n")
        if not fname in self.fname2classes:
            self.logging.write("..no classes\n")
            return
        source = open(fname).read()
        for class_full_name in self.fname2classes[fname]:
            type_param_names, package_name, imports, extends_parsed_strs, (class_start, class_end, fname) = self.all_classes_decls[class_full_name]
            class_node = [node for node in all_nodes(file_node) if node.start == class_start and node.end == class_end][0]
            method_declarations = [node for node in class_node.children \
                                            if set(["body.MethodDeclaration", "body.ConstructorDeclaration"]) & node.labels]

            class_variables = find_all_var_declarations(class_node, source)

            for method_decl_node in method_declarations:
                for log_call_stack in self.extract_log_calls_from_method_declartion(method_decl_node, source):
                    log_call_snippet = log_call_stack[-1].get_snippet(source).replace("\n", " ")
                    self.logging.write("[LOG CALL] " +
                                       str((log_call_stack[-1].start, log_call_stack[-1].end)) + " " + log_call_snippet + "\n")
                    self.logging.flush()

                    def get_var_type_func(node, fname=fname):
                        key = (fname, node.start, node.end)
                        if key in self.full_type_markup and type(self.full_type_markup[key]) == tuple:
                            return self.full_type_markup[key][0]
                        return None

                    unrolled_log_line_elements = self.get_log_line_constitutes(log_call_stack, source, fname, class_full_name,
                                                                               class_node, get_var_type_func)

                    #simple filter from explosions
                    if len(unrolled_log_line_elements) > MAX_NUMBER_OF_CHAINS_PER_LOGLINE:
                        self.logging.write("Trimmed, as the number of resolved chains %d > %d\n" %
                                                            (len(unrolled_log_line_elements),
                                                             MAX_NUMBER_OF_CHAINS_PER_LOGLINE))
                        unrolled_log_line_elements = unrolled_log_line_elements[:MAX_NUMBER_OF_CHAINS_PER_LOGLINE]

                    if 1:
                        unrolled_log_line_elements_merged = []
                        if 1:
                            for unrolled_param_set in unrolled_log_line_elements:
                                final_set_of_nodes = []
                                first_param_nodes = unrolled_param_set[0]
                                used_params = set()
                                curr_param_index = 1
                                added_param_sets = 0
                                for node in first_param_nodes:
                                    if type(node) != str:
                                        final_set_of_nodes.append(node)
                                        continue
                                    string_constant = node
                                    placeholders = re.findall("\{[0-9]*\}", string_constant)
                                    # print placeholders, [string_constant], unrolled_param_set
                                    for placeholder in placeholders:
                                        plhld_pos = string_constant.find(placeholder)
                                        prefix, string_constant = string_constant[:plhld_pos], string_constant[
                                                                                               plhld_pos + len(placeholder):]
                                        if prefix:
                                            final_set_of_nodes.append(prefix)
                                        if placeholder[1:-1]:
                                            curr_param_index = int(placeholder[1:-1]) + 1

                                        if curr_param_index >= len(unrolled_param_set):
                                            #raise Exception()
                                            curr_param_index = len(unrolled_param_set) - 1
                                        used_params.add(curr_param_index)
                                        final_set_of_nodes += unrolled_param_set[curr_param_index]
                                        added_param_sets += 1
                                        curr_param_index += 1
                                    if string_constant:
                                        final_set_of_nodes.append(string_constant)
                                for param_index in xrange(1, len(unrolled_param_set)):
                                    if not param_index in used_params:
                                        final_set_of_nodes += unrolled_param_set[param_index]
                                        added_param_sets += 1
                                #if added_param_sets + 1 != len(unrolled_param_set):
                                #    raise Exception()
                                unrolled_log_line_elements_merged += [final_set_of_nodes]

                        for log_line_nodes in unrolled_log_line_elements_merged:
                            log_chunks = []
                            for elem in log_line_nodes:
                                #print "elem", elem
                                if type(elem) == str:
                                    log_chunks += [("SC", "String", elem)]
                                    continue
                                node, node_source, node_fname, node_class_full_name = elem
                                if node == THIS:
                                    log_chunks += [("VR", node_class_full_name, "this")]
                                elif set(["expr.SimpleName", "expr.NameExpr"]) & node.labels:
                                    node_type = get_var_type_func(node, node_fname)
                                    node_snippet = node.get_snippet(node_source).strip().replace("\n", " ")
                                    log_chunks += [("VR", str(node_type), node_snippet)]
                                elif "expr.MethodCallExpr" in node.labels or "expr.FieldAccessExpr" in node.labels:
                                    caller_type = None
                                    node_snippet = node.get_snippet(node_source).strip().replace("\n", " ")
                                    if node_snippet.find("(") > 0 and node_snippet.find("(") < node.get_snippet(node_source).find(
                                            ".") or node.get_snippet(node_source).find(".") < 0:
                                        caller_type = node_class_full_name
                                    else:
                                        caller = node
                                        while caller.children:
                                            caller = caller.children[0]
                                        caller_snippet = caller.get_snippet(node_source).strip()
                                        if "expr.ThisExpr" in caller.labels:
                                            caller_type = node_class_full_name
                                        elif caller_snippet.startswith("org.") or caller_snippet.startswith("java.") or \
                                                caller_snippet[0].isupper():
                                            caller_type = caller_snippet
                                        else:
                                            caller_type = get_var_type_func(caller, node_fname)
                                    log_chunks += [("MC", str(caller_type), node_snippet)]
                                else:
                                    log_chunks += [("UN", "", node.get_snippet(node_source).strip().replace("\n", " "))]

                            template = {"class": class_full_name, "package": package_name, "source": fname,  "chunks": log_chunks, "logcall": log_call_snippet}
                            import json
                            self.output.write(json.dumps(template) + "\n")
                            self.output.flush()


if __name__ == "__main__":
    import sys
    import os
    try:
        index_location, output_loc = sys.argv[1:]
    except:
        print "usage: python extract_log_templates.py <folder with indices> <output filename or - > [-d]"
        exit()
        #index_location, output_loc = "/home/arslan/src/tmp", "templates.json"
    LogExtractor(index_location, output_loc)


