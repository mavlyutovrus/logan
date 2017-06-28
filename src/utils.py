import re
import sys

sys.setrecursionlimit(100000)

def fname2code(fname):
    import hashlib
    m = hashlib.md5()
    m.update(fname)
    return m.hexdigest()

default_classes = set(["Appendable", "AutoCloseable", "CharSequence", "Cloneable", "Comparable", "Iterable", "Readable",
                       "Runnable", "Thread.UncaughtExceptionHandler", "Boolean", "Byte", "Character",
                       "Character.Subset",
                       "Character.UnicodeBlock", "Class", "ClassLoader", "ClassValue", "Compiler", "Double", "Enum", "EnumSet",
                       "Float",
                       "InheritableThreadLocal", "Integer", "Long", "Math", "Number", "Object", "Package", "Process",
                       "ProcessBuilder", "ProcessBuilder.Redirect", "Runtime", "RuntimePermission", "SecurityManager",
                       "Short",
                       "StackTraceElement", "StrictMath", "String", "StringBuffer", "StringBuilder", "System", "Thread",
                       "ThreadGroup", "ThreadLocal", "Throwable", "Void", "Character.UnicodeScript",
                       "ProcessBuilder.Redirect.Type",
                       "Thread.State", "ArithmeticException", "ArrayIndexOutOfBoundsException", "ArrayStoreException",
                       "ClassCastException", "ClassNotFoundException", "CloneNotSupportedException",
                       "EnumConstantNotPresentException",
                       "Exception", "IllegalAccessException", "IllegalArgumentException",
                       "IllegalMonitorStateException",
                       "IllegalStateException", "IllegalThreadStateException", "IndexOutOfBoundsException",
                       "InstantiationException",
                       "InterruptedException", "NegativeArraySizeException", "NoSuchFieldException",
                       "NoSuchMethodException",
                       "NullPointerException", "NumberFormatException", "ReflectiveOperationException",
                       "RuntimeException",
                       "SecurityException", "StringIndexOutOfBoundsException", "TypeNotPresentException",
                       "UnsupportedOperationException", "AbstractMethodError", "AssertionError", "BootstrapMethodError",
                       "ClassCircularityError", "ClassFormatError", "Error", "ExceptionInInitializerError",
                       "IllegalAccessError",
                       "IncompatibleClassChangeError", "InstantiationError", "InternalError", "LinkageError",
                       "NoClassDefFoundError", "NoSuchFieldError", "NoSuchMethodError", "OutOfMemoryError",
                       "StackOverflowError", "ThreadDeath", "UnknownError", "UnsatisfiedLinkError",
                       "UnsupportedClassVersionError",
                       "VerifyError", "VirtualMachineError", "Deprecated", "Override", "SafeVarargs",
                       "SuppressWarnings"])

primitive_types = set(["boolean", "char", "byte", "short", "int", "long", "float", "double"])

java_default_classes = set([
    "java.util.regex.Pattern",
    "java.util.Collection", "java.util.Comparator", "java.util.Deque", "java.util.Enumeration",
    "java.util.EventListener", \
    "java.util.Formattable", "java.util.Iterator", "java.util.List", "java.util.ListIterator",
    "java.util.Map", "java.util.Map.Entry", \
    "java.util.NavigableMap", "java.util.NavigableSet", "java.util.Observer", "java.util.Queue",
    "java.util.RandomAccess", "java.util.Set", \
    "java.util.SortedMap", "java.util.SortedSet", "java.util.AbstractCollection",
    "java.util.AbstractList", "java.util.AbstractMap", \
    "java.util.AbstractMap.SimpleEntry", "java.util.AbstractMap.SimpleImmutableEntry",
    "java.util.AbstractQueue", "java.util.AbstractSequentialList", \
    "java.util.AbstractSet", "java.util.ArrayDeque", "java.util.ArrayList", "java.util.Arrays",
    "java.util.BitSet", "java.util.Calendar", \
    "java.util.Collections", "java.util.Currency", "java.util.Date", "java.util.Dictionary",
    "java.util.EventObject", "java.util.FormattableFlags", \
    "java.util.Formatter", "java.util.GregorianCalendar", "java.util.HashMap",
    "java.util.HashSet", "java.util.Hashtable", \
    "java.util.IdentityHashMap", "java.util.LinkedHashMap", "java.util.LinkedHashSet",
    "java.util.LinkedList", "java.util.ListResourceBundle", \
    "java.util.Locale", "java.util.Locale.Builder", "java.util.Objects", "java.util.Observable",
    "java.util.PriorityQueue", \
    "java.util.Properties", "java.util.PropertyPermission", "java.util.PropertyResourceBundle",
    "java.util.Random", "java.util.ResourceBundle", \
    "java.util.ResourceBundle.Control", "java.util.Scanner", "java.util.ServiceLoader",
    "java.util.SimpleTimeZone", "java.util.Stack", \
    "java.util.StringTokenizer", "java.util.Timer", "java.util.TimerTask", "java.util.TimeZone",
    "java.util.TreeMap", "java.util.TreeSet", \
    "java.util.UUID", "java.util.Vector", "java.util.WeakHashMap", "java.util.Locale.Category",
    "java.util.ConcurrentModificationException", \
    "java.util.DuplicateFormatFlagsException", "java.util.EmptyStackException",
    "java.util.FormatFlagsConversionMismatchException", \
    "java.util.FormatterClosedException", "java.util.IllegalFormatCodePointException",
    "java.util.IllegalFormatConversionException", \
    "java.util.IllegalFormatException", "java.util.IllegalFormatFlagsException",
    "java.util.IllegalFormatPrecisionException", \
    "java.util.IllegalFormatWidthException", "java.util.IllformedLocaleException",
    "java.util.InputMismatchException", \
    "java.util.InvalidPropertiesFormatException", "java.util.MissingFormatArgumentException",
    "java.util.MissingFormatWidthException", \
    "java.util.MissingResourceException", "java.util.NoSuchElementException",
    "java.util.TooManyListenersException", \
    "java.util.UnknownFormatConversionException", "java.util.UnknownFormatFlagsException",
    "java.util.ServiceConfigurationError", \
    "java.io.Closeable", "java.io.DataInput", "java.io.DataOutput", "java.io.Externalizable",
    "java.io.FileFilter", \
    "java.io.FilenameFilter", "java.io.Flushable", "java.io.ObjectInput",
    "java.io.ObjectInputValidation", "java.io.ObjectOutput", \
    "java.io.ObjectStreamConstants", "java.io.Serializable", "java.io.BufferedInputStream",
    "java.io.BufferedOutputStream", \
    "java.io.BufferedReader", "java.io.BufferedWriter", "java.io.ByteArrayInputStream",
    "java.io.ByteArrayOutputStream", \
    "java.io.CharArrayReader", "java.io.CharArrayWriter", "java.io.Console",
    "java.io.DataInputStream", "java.io.DataOutputStream", \
    "java.io.File", "java.io.FileDescriptor", "java.io.FileInputStream",
    "java.io.FileOutputStream", "java.io.FilePermission", \
    "java.io.FileReader", "java.io.FileWriter", "java.io.FilterInputStream",
    "java.io.FilterOutputStream", "java.io.FilterReader", \
    "java.io.FilterWriter", "java.io.InputStream", "java.io.InputStreamReader",
    "java.io.LineNumberReader", \
    "java.io.ObjectInputStream", "java.io.ObjectInputStream.GetField",
    "java.io.ObjectOutputStream", \
    "java.io.ObjectOutputStream.PutField", "java.io.ObjectStreamClass",
    "java.io.ObjectStreamField", "java.io.OutputStream", \
    "java.io.OutputStreamWriter", "java.io.PipedInputStream", "java.io.PipedOutputStream",
    "java.io.PipedReader", \
    "java.io.PipedWriter", "java.io.PrintStream", "java.io.PrintWriter",
    "java.io.PushbackInputStream", "java.io.PushbackReader", \
    "java.io.RandomAccessFile", "java.io.Reader", "java.io.SequenceInputStream",
    "java.io.SerializablePermission", \
    "java.io.StreamTokenizer", "java.io.StringReader", "java.io.StringWriter", "java.io.Writer",
    "java.io.CharConversionException", \
    "java.io.EOFException", "java.io.FileNotFoundException", "java.io.InterruptedIOException",
    "java.io.InvalidClassException", \
    "java.io.InvalidObjectException", "java.io.IOException", "java.io.NotActiveException",
    "java.io.NotSerializableException", \
    "java.io.ObjectStreamException", "java.io.OptionalDataException",
    "java.io.StreamCorruptedException", \
    "java.io.SyncFailedException", "java.io.UnsupportedEncodingException",
    "java.io.UTFDataFormatException", \
    "java.io.WriteAbortedException", "java.io.IOError", \
    "java.util.concurrent.ArrayBlockingQueue", "java.util.concurrent.ThreadPoolExecutor",
    "java.util.concurrent.TimeUnit",
    "java.net.ContentHandlerFactory", "java.net.CookiePolicy", "java.net.CookieStore",
    "java.net.DatagramSocketImplFactory", "java.net.FileNameMap", "java.net.ProtocolFamily",
    "java.net.SocketImplFactory", "java.net.SocketOption", "java.net.SocketOptions",
    "java.net.URLStreamHandlerFactory", "java.net.Authenticator", "java.net.CacheRequest",
    "java.net.CacheResponse", "java.net.ContentHandler", "java.net.CookieHandler",
    "java.net.CookieManager", "java.net.DatagramPacket", "java.net.DatagramSocket",
    "java.net.DatagramSocketImpl", "java.net.HttpCookie", "java.net.HttpURLConnection",
    "java.net.IDN", "java.net.Inet4Address", "java.net.Inet6Address", "java.net.InetAddress",
    "java.net.InetSocketAddress", "java.net.InterfaceAddress", "java.net.JarURLConnection",
    "java.net.MulticastSocket", "java.net.NetPermission", "java.net.NetworkInterface",
    "java.net.PasswordAuthentication", "java.net.Proxy", "java.net.ProxySelector",
    "java.net.ResponseCache", "java.net.SecureCacheResponse", "java.net.ServerSocket",
    "java.net.Socket", "java.net.SocketAddress", "java.net.SocketImpl",
    "java.net.SocketPermission", "java.net.StandardSocketOptions", "java.net.URI",
    "java.net.URL", "java.net.URLClassLoader", "java.net.URLConnection", "java.net.URLDecoder",
    "java.net.URLEncoder", "java.net.URLStreamHandler", "java.net.Authenticator.RequestorType",
    "java.net.Proxy.Type", "java.net.StandardProtocolFamily", "java.net.BindException",
    "java.net.ConnectException", "java.net.HttpRetryException",
    "java.net.MalformedURLException", "java.net.NoRouteToHostException",
    "java.net.PortUnreachableException", "java.net.ProtocolException",
    "java.net.SocketException", "java.net.SocketTimeoutException",
    "java.net.UnknownHostException", "java.net.UnknownServiceException",
    "java.net.URISyntaxException",
    "java.util.concurrent.AbstractExecutorService", "java.util.concurrent.ArrayBlockingQueue",
    "java.util.concurrent.BlockingDeque", "java.util.concurrent.BlockingQueue",
    "java.util.concurrent.BrokenBarrierException", "java.util.concurrent.Callable",
    "java.util.concurrent.CancellationException", "java.util.concurrent.CompletionService",
    "java.util.concurrent.ConcurrentHashMap", "java.util.concurrent.ConcurrentLinkedDeque",
    "java.util.concurrent.ConcurrentLinkedQueue", "java.util.concurrent.ConcurrentMap",
    "java.util.concurrent.ConcurrentNavigableMap", "java.util.concurrent.ConcurrentSkipListMap",
    "java.util.concurrent.ConcurrentSkipListSet", "java.util.concurrent.CopyOnWriteArrayList",
    "java.util.concurrent.CopyOnWriteArraySet", "java.util.concurrent.CountDownLatch",
    "java.util.concurrent.CyclicBarrier", "java.util.concurrent.Delayed", "java.util.concurrent.Exchanger",
    "java.util.concurrent.ExecutionException", "java.util.concurrent.Executor",
    "java.util.concurrent.ExecutorCompletionService", "java.util.concurrent.ExecutorService",
    "java.util.concurrent.Executors", "java.util.concurrent.ForkJoinPool",
    "java.util.concurrent.ForkJoinPool.ForkJoinWorkerThreadFactory", "java.util.concurrent.ForkJoinPool.ManagedBlocker",
    "java.util.concurrent.ForkJoinTask", "java.util.concurrent.ForkJoinWorkerThread", "java.util.concurrent.Future",
    "java.util.concurrent.FutureTask", "java.util.concurrent.LinkedBlockingDeque",
    "java.util.concurrent.LinkedBlockingQueue", "java.util.concurrent.LinkedTransferQueue",
    "java.util.concurrent.Phaser", "java.util.concurrent.PriorityBlockingQueue", "java.util.concurrent.RecursiveAction",
    "java.util.concurrent.RecursiveTask", "java.util.concurrent.RejectedExecutionException",
    "java.util.concurrent.RejectedExecutionHandler", "java.util.concurrent.RunnableFuture",
    "java.util.concurrent.RunnableScheduledFuture", "java.util.concurrent.ScheduledExecutorService",
    "java.util.concurrent.ScheduledFuture", "java.util.concurrent.ScheduledThreadPoolExecutor",
    "java.util.concurrent.Semaphore", "java.util.concurrent.SynchronousQueue", "java.util.concurrent.ThreadFactory",
    "java.util.concurrent.ThreadLocalRandom", "java.util.concurrent.ThreadPoolExecutor",
    "java.util.concurrent.ThreadPoolExecutor.AbortPolicy", "java.util.concurrent.ThreadPoolExecutor.CallerRunsPolicy",
    "java.util.concurrent.ThreadPoolExecutor.DiscardOldestPolicy",
    "java.util.concurrent.ThreadPoolExecutor.DiscardPolicy", "java.util.concurrent.TimeUnit",
    "java.util.concurrent.TimeoutException", "java.util.concurrent.TransferQueue",
    "Pack200.Packer", "Pack200.Unpacker", "Attributes", "Attributes.Name", "JarEntry", "JarFile", "JarInputStream",
    "JarOutputStream", "Manifest", "Pack200", "JarException"
])

external_libs_classes = set(["org.apache.zookeeper.AsyncCallback.StringCallback", "org.apache.zookeeper.AsyncCallback.StatCallback"])

all_default_classes = external_libs_classes | java_default_classes | primitive_types | default_classes


CLASS_LABELS = set(['body.ClassOrInterfaceDeclaration', 'body.EnumDeclaration',
                    'body.ClassDeclaration', 'body.InterfaceDeclaration', 'body.AnnotationDeclaration'])

METHOD_DECL_LABELS = set(["body.MethodDeclaration", "body.ConstructorDeclaration"])

COMMENTS_LABELS = set(['comments.LineComment', 'comments.BlockComment'])


def is_statement(node):
    if not node:
        return False
    for label in node.labels:
        if label.startswith("stmt."):
            return True
    return False


def decompose_method_call(node, source):
    if not "expr.MethodCallExpr" in node.labels:
        return (None, None, None, [])
    snippet = node.get_snippet(source)
    param_nodes = []
    caller_node = None
    method_type_values_nodes = []
    method_name_node = None
    elems = [elem for elem in node.children if not set(['comments.LineComment', 'comments.BlockComment']) & elem.labels]
    if len(elems) == 1:
        return (None, elems[0], [], [])

    def remove_comment_lines(text):
        import re
        text = "\n".join(chunk.split("//")[0] for chunk in text.split("\n"))
        text = re.subn("/\*.+?\*/", " ", text.replace("\n", " "))[0]
        return text

    delimiter = ""
    type_params_exist = False
    if 1:
        first_child = elems[0]
        second_child = elems[1]
        delimiter = snippet[first_child.end - node.start:second_child.start - node.start]
        delimiter = remove_comment_lines(delimiter)
        if "<" in delimiter:
            type_params_exist = True
        delimiter = delimiter.replace("<", " ")
        delimiter = delimiter.strip()

    if delimiter == ".":
        caller_node = elems[0]
        elems = elems[1:]
    elif delimiter == "(":
        caller_node = None
    else:
        raise Exception("can't parse method call", "unknown delimiter: \"" + delimiter + "\"")

    if type_params_exist:
        while True:
            head = elems[0]
            method_type_values_nodes.append(head)
            elems = elems[1:]
            delimiter = snippet[head.end - node.start: elems[0].start - node.start]
            delimiter = remove_comment_lines(delimiter).strip()
            if delimiter == ">" or not delimiter:
                break
            elif delimiter != ",":
                #print node.get_snippet(source)
                #print [head.get_snippet(source)]
                raise Exception("can't parse method call", "unknown delimiter for type params: [" + delimiter + "]")
                break
    method_name_node = elems[0]
    if not 'expr.SimpleName' in method_name_node.labels:
        raise Exception("can't parse method call", "complex method name")
    param_nodes = elems[1:]
    for param_index in xrange(1, len(param_nodes)):
        prev = param_nodes[param_index - 1]
        next = param_nodes[param_index]
        delimiter = snippet[prev.end - node.start : next.start - node.start]
        import re
        delimiter = "\n".join(chunk.split("//")[0] for chunk in delimiter.split("\n"))
        delimiter = re.subn("/\*.+?\*/", " ", delimiter.replace("\n", " "))[0]
        delimiter = delimiter.strip()
        #if delimiter != ",":
        if not "," in delimiter:
            print node.get_snippet(source)
            raise Exception("can't parse method call", "unknown delimiter for method params: [" + delimiter + "]")
    return (caller_node, method_name_node, method_type_values_nodes, param_nodes)


"""class_name, type_parameters_parsed, extends_parsed_strs"""
def parse_class_declaration(class_node, source):
    header_nodes = []
    type_parameters = []
    extends = []
    for child in class_node.children:
        if set(['expr.MarkerAnnotationExpr', 'expr.SingleMemberAnnotationExpr',
                'expr.NormalAnnotationExpr', 'comments.JavadocComment',
                'comments.LineComment', 'comments.BlockComment']) & child.labels:
            continue
        if child.labels & set(['body.ClassOrInterfaceDeclaration', 'body.EnumDeclaration',
                                'body.ClassDeclaration', 'body.InterfaceDeclaration',
                                "body.MethodDeclaration", "body.ConstructorDeclaration",
                               'body.EnumConstantDeclaration', 'body.FieldDeclaration',
                               'body.AnnotationDeclaration', 'body.EmptyMemberDeclaration',
                               'body.AnnotationMemberDeclaration']):
            break
        if 'body.InitializerDeclaration' in child.labels:
            #TODO process this part also
            break
        header_nodes.append(child)
    class_name = header_nodes[0]
    tail_nodes = header_nodes[1:]
    if not 'expr.SimpleName' in class_name.labels:
        raise Exception("can't parse class definition", "unknown chunk [" + class_name.get_snippet(source) + "]")
    while tail_nodes and 'type.TypeParameter' in tail_nodes[0].labels:
        type_parameters += [tail_nodes[0]]
        tail_nodes = tail_nodes[1:]
    while tail_nodes and 'type.ClassOrInterfaceType' in tail_nodes[0].labels:
        extends += [tail_nodes[0]]
        tail_nodes = tail_nodes[1:]
    if tail_nodes:
        print tail_nodes[0].labels
        raise Exception("can't parse class definition", "unknown tail [" + tail_nodes[0].get_snippet(source) + "]")

    type_parameters_parsed = []
    for type_node in type_parameters:
        class_name_node = type_node
        type_node_extends = []
        if type_node.children:
            class_name_node = type_node.children[0]
            type_node_extends = type_node.children[1:]
            if not 'expr.SimpleName' in class_name_node.labels or \
                    [1 for snode in type_node_extends if not 'type.ClassOrInterfaceType' in snode.labels]:
                raise Exception("can't parse class type parameter",
                                type_node.get_snippet(source))
        type_parameters_parsed.append((class_name_node, type_node_extends))

    extends_parsed_strs = [] #as text
    for extend_node in extends:
        #TODO: at the moment the overhead for considering type parameters of extending classes is too big
        #cases like "Mapper<KEYIN, VALUEIN, KEYOUT, VALUEOUT>.Context"
        #so we just cut them, in case if needed, I leave here a full code, that tackle all cases except the aforementioned
        """
        extend_node_snippet = extend_node.get_snippet(source).replace("\n", " ")
        def split_param_types(snippet):
            if not "<" in snippet:
                return (snippet.strip(), [])
            class_name, param_list_str = snippet[:snippet.find("<")], snippet[snippet.find("<") + 1:]
            if not param_list_str.endswith(">"):
                print snippet
                raise Exception("hmmmm")
            param_list_str = param_list_str[:-1]
            param_list = []
            open_tags = 0
            start = 0
            for pos in xrange(len(param_list_str)):
                if param_list_str[pos] == "<":
                    open_tags += 1
                elif param_list_str[pos] == ">":
                    open_tags -= 1
                    if open_tags == 0:
                        param_list += [param_list_str[start:pos + 1]]
                        start = pos + 1
            if param_list_str[start:].strip():
                param_list.append(param_list_str[start:])
            param_list = [split_param_types(param) for param in param_list]
            return (class_name, param_list)
        extends_parsed_strs  += [split_param_types(extend_node_snippet)]
        """
        no_types = extend_node.get_snippet(source).replace("\n", "").replace("\t", "").replace(" ", "")
        open_tags_count = len(no_types.split("<")) - 1
        close_tags_count = len(no_types.split(">")) - 1
        if open_tags_count != close_tags_count:
            raise Exception("unbalanced type bracets", no_types)
        iter = 0
        while "<" in no_types or ">" in no_types:
            no_types = re.subn("<[^<>]*>", "", no_types)[0]
            iter += 1
            if iter > 10:
                break
        if iter > 10:
            raise Exception("unbalanced type bracets", no_types)
        extends_parsed_strs += [no_types]
    return (class_name, type_parameters_parsed, extends_parsed_strs)



def remove_comments(source_txt):
    orig_source_len = len(source_txt)

    while "\\\\" in source_txt:
        source_txt = source_txt.replace("\\\\", "||")
    while "\\\"" in source_txt:
        source_txt = source_txt.replace("\\\"", "||")
    while "\\'" in source_txt:
        source_txt = source_txt.replace("\\'", "||")
    while "\\\n" in source_txt:
        source_txt = source_txt.replace("\\\n", "||")

    one_line_comment = False
    multi_line_comment = False
    string_constant1 = False
    string_constant2 = False
    filtered = ""
    prev = ""
    for curr in source_txt:
        if curr == "\n":
            one_line_comment = False
            string_constant1 = False
            string_constant2 = False
        elif curr == "*":
            if prev == "/":
                if one_line_comment or string_constant1 or string_constant2:
                    pass
                else:
                    multi_line_comment = True
                    filtered = filtered[:-1] + " "
        elif curr == "/":
            if prev == "*":
                if multi_line_comment:
                    multi_line_comment = False
                    curr = " "
            elif prev == "/":
                if one_line_comment or string_constant2 or string_constant1 or multi_line_comment:
                    pass
                else:
                    one_line_comment = True
                    filtered = filtered[:-1] + " "
        elif curr == "\"":
            if one_line_comment or multi_line_comment or string_constant2:
                pass
            else:
                string_constant1 = not string_constant1
                if not string_constant1:
                    curr = " "
        elif curr == "'":
            if one_line_comment or multi_line_comment or string_constant1:
                pass
            else:
                string_constant2 = not string_constant2
                if string_constant2:
                    curr = " "
        prev = curr
        if multi_line_comment or one_line_comment or string_constant1 or string_constant2:
            filtered += " "
        else:
            filtered += prev

    source_txt = filtered

    for comment in re.findall("\/\*.+?\*\/", source_txt.replace("\n", "<NNNNNNNN>")):
        comment = comment.replace("<NNNNNNNN>", "\n")
        raise Exception("Parsing issue", "Not able to remove comments properly.")

    for comment in re.findall("\/\/.+", source_txt):
        #print comment
        raise Exception("Parsing issue", "Not able to remove comments properly.")

    if orig_source_len != len(source_txt):
        raise Exception("Parsing issue", "Not able to remove comments properly.")
    return source_txt


def get_line_offsets(source):
    line_offsets = [len(line) + 1 for line in source.split("\n")]
    for index in xrange(1, len(line_offsets)):
        line_offsets[index] += line_offsets[index - 1]
    line_offsets = [0] + line_offsets
    return line_offsets


def remove_interfaces(sample):
    interface_openned = False
    depth = 0
    filtered = ""
    for pos in xrange(len(sample)):
        if sample[pos] == "@":
            if not interface_openned:
                interface_openned = True
                depth = 0
        elif sample[pos] == "\n":
            if depth == 0:
                interface_openned = False
        elif interface_openned:
            if sample[pos] in "{(":
                depth += 1
            elif sample[pos] in ")}":
                depth -= 1
        if not interface_openned:
            filtered += sample[pos]
        else:
            filtered += " "
    return filtered

def a_in_b(a, b):
    return a[0] >= b[0] and a[1] <= b[1]


def FromString2Node(string):
    nodes = []
    for chunk in string.split("|||"):
        chunk = chunk.strip()
        if not chunk:
            continue
        start, end, labels = chunk.split("<>")
        start, end = int(start), int(end)
        labels = set([label for label in labels.split("|") if label])
        nodes.append(TNode(start, end, labels))
    abs_start = min([node.start for node in nodes])
    abs_end = max([node.end for node in nodes])
    root = [node for node in nodes if node.start  == abs_start and node.end == abs_end][0]
    nodes = [node for node in nodes if node != root]
    nodes = sorted(nodes, key=lambda node : (node.start, -node.end + node.start,))
    stack = [root]
    for node in nodes:
        while node.start >= stack[-1].end:
            stack.pop()
        stack[-1].children.append(node)
        stack.append(node)
    return root


class TNode:
    def __init__(self, start, end, labels):
        self.start = start
        self.end = end
        self.labels = set(labels)
        self.children = []

    def ToString(self):
        output = str(self.start) + "<>" + str(self.end) + "<>" + "|".join(self.labels) + "|||"
        for child in self.children:
            output += child.ToString()
        return output

    def size(self):
        return 1 + sum(child.size() for child in self.children)

    def DFS(self, stack, func):
        stack.append(self)
        #print len(stack),
        func(stack)
        for child in self.children:
            child.DFS(stack, func)
        stack.pop()

    def DFS1(self, stack, func):
        stack.append(self)
        #print len(stack),
        go_deeper = func(stack)
        if go_deeper:
            for child in self.children:
                child.DFS1(stack, func)
        stack.pop()

    def get_snippet(self, source):
        return source[self.start:self.end]

    def find_subnode(self, start, end):
        if self.start == start and self.end == end:
            return self
        for child in self.children:
            if child.start <= start and child.end >= end:
                return child.find_subnode(start, end)
        return None

    """ other_markup - list of (start, end, labels, color), labels - set, color - str to highlight """
    def create_html(self, source, other_markup):
        offset = self.start
        intervals = other_markup + \
               [(node.start, node.end, node.labels, "") for node in all_nodes(self)]
        borders = []
        for start, end, labels, color in intervals:
            borders.append( (end, 0, labels, color) )
            borders.append((start, 1, labels, color))
        borders.sort()
        borders += [(self.end, 0, set(), "")]
        labels_freqs = {}
        colors_stack = []
        prev_border = offset
        markup_intervals = []
        for border, is_open, labels, color in borders:
            if border != prev_border:
                markup_intervals += [(prev_border,
                                      border,
                                      sorted(labels_freqs.keys()),
                                      colors_stack and colors_stack[-1] or "")]
                prev_border = border
            if is_open:
                for label in labels:
                    labels_freqs.setdefault(label, 0)
                    labels_freqs[label] += 1
                if color:
                    colors_stack.append(color)
            else:
                for label in labels:
                    labels_freqs[label] -= 1
                    if not labels_freqs[label]:
                        del labels_freqs[label]
                if color:
                    colors_stack.pop()
        html = "<html><head><meta charset=\"UTF-8\"></head><body style=\"font-family: monospace; \">\n"
        for start, end, tags, color in markup_intervals:
            tags.sort()
            chunk  = source[start:end].replace("<", "&lt;").replace(">", "&gt;")
            chunk = chunk.replace("\n", "\n<br/>")
            chunk = chunk.replace(" ", "&nbsp;").replace("\t", "&nbsp;")
            html += "<span title=\"" +  ";".join(tags).replace("\"", "'") + "\"" +   \
                    (color and "style=\"background-color:" + color + "; \"" or "")      \
                    + ">" + chunk + "</span>"
        html += "\n</body></html>"
        return html


def build_path(node, root):
    path = [root]
    while path[-1] != node:
        matched = False
        for child in path[-1].children:
            if child.start <= node.start and child.end >= node.end:
                path.append(child)
                matched = True
                break
        if not matched:
            raise Exception("build_path", "node is not in root subtree")
    return path

def get_parent(node, root):
    if node == root:
        return None
    parent = root
    stack = []
    while parent != node:
        stack.append(parent)
        matched = False
        for child in parent.children:
            if child.start == node.start and child.end == node.end:
                return parent
            if child.start <= node.start and child.end >= node.end:
                parent = child
                matched = True
                break
        if not matched:
            """
            print [(elem.start, elem.end) for elem in stack]
            print stack[-1].children, stack[-1].start, stack[-1].end
            for child in parent.children:
                print "\t", child.start, child.end
            print node.start, node.end, root.start, root.end
            """
            raise Exception("get_parent", "node is not in root subtree")
    return None


def all_nodes(node):
    layer = [node]
    while layer:
        new_layer = []
        for node in layer:
            new_layer += node.children
            yield node
        layer = new_layer

def is_class_def(node):
    if node.labels & set(['body.ClassOrInterfaceDeclaration', 'body.EnumDeclaration',
                                                 'body.ClassDeclaration', 'body.InterfaceDeclaration',
                                                 'body.AnnotationDeclaration']):
        return True
    return False


def all_nodes_post_order(node):
    stack = []
    while node or stack:
        if node:
            stack.append(node)
            node = node.children and node.children[0] or None
            continue
        node = stack.pop()
        yield node
        if stack:
            for child_index in xrange(len(stack[-1].children)):
                if stack[-1].children[child_index] == node:
                    node = child_index + 1 < len(stack[-1].children) and stack[-1].children[child_index + 1] or None
                    break
        else:
            break



def markup2tree(markup, source=None):
    used = set()
    root = TNode(0, 1000000, set())
    stack = [root]
    intervals = markup.keys()
    while True:
        intervals = sorted(intervals, key=lambda interval : (interval[0], -interval[1]+interval[0],))
        fixed = False
        for first in xrange(len(intervals)):
            if fixed:
                break
            for second in xrange(first + 1, len(intervals)):
                if intervals[second][0] >= intervals[first][1]:
                    break
                if intervals[second][0] < intervals[first][1] and intervals[second][1] > intervals[first][1]:
                    #known issue -> fix
                    """
                    if 'type.ArrayType' in markup[intervals[first]] and 'body.VariableDeclarator' in markup[intervals[second]]:
                        #print markup[intervals[second]]
                        del markup[intervals[second]]
                        intervals = intervals[:second] + intervals[second + 1:]
                        fixed = True
                        break
                    elif 'type.ArrayType' in markup[intervals[first]] and 'expr.SimpleName' in markup[intervals[second]]:
                        update_interval = (intervals[second][0], intervals[first][1])
                        update_interval_labels = markup[intervals[second]]
                        del markup[intervals[second]]
                        intervals[second] = update_interval
                        markup[update_interval] = update_interval_labels
                    """
                    if 'type.ArrayType' in markup[intervals[first]] and set(['body.VariableDeclarator', 'expr.SimpleName']) & markup[intervals[second]]:
                        update_interval = (intervals[first][0], intervals[second][0])
                        update_interval_labels = markup[intervals[first]]
                        del markup[intervals[first]]
                        if update_interval in markup:
                            markup[update_interval] = markup[update_interval]  | update_interval_labels
                            intervals[first] = intervals[-1]
                            intervals.pop()
                        else:
                            intervals[first] = update_interval
                            markup[update_interval] = update_interval_labels
                        fixed = True
                        break
                    else:
                        #print intervals[first], "||", source[intervals[first][0]:intervals[first][1]], "||", markup[intervals[first]]
                        #print intervals[second], "||", source[intervals[second][0]:intervals[second][1]], "||", markup[intervals[second]]
                        raise Exception("mishup in markup", "can't resolve")
        if not fixed:
            break
    for interval in intervals:
        while interval[0] >= stack[-1].end:
            stack.pop()
        if interval[1] > stack[-1].end:
            print "ASDASDASDAF", interval, (stack[-1].start, stack[-1].end)
        node = TNode(interval[0], interval[1], set(markup[interval]))
        stack[-1].children.append(node)
        stack.append(node)
    if root.size() != len(markup) + 1:
        #print "Mismatch", root.size(), len(markup)
        raise Exception("mishup in markup", "can't resolve")

    for node in all_nodes(root):
        start = node.start
        for child in node.children:
            if child.start < start or child.end > node.end:
                raise Exception("mallformed node tree", "")
            start = child.end
    return root

def cortesian_sum(list_of_lists):
    if not list_of_lists:
        return []
    all_chains = list_of_lists[0]
    for next_list in list_of_lists[1:]:
        new_all_chains = []
        for chain in all_chains:
            for value in next_list:
                new_all_chains += [chain + value]
        all_chains = new_all_chains
    return all_chains


def might_be_variable_name(node, parent, source=None):
    if not set(["expr.SimpleName", "expr.NameExpr"]) & node.labels:
        return False
    for child_index in xrange(len(parent.children)):
        if parent.children[child_index] == node:
            break
    if "expr.MethodCallExpr" in parent.labels and child_index == 1:
        return False
    if "body.MethodDeclaration" in parent.labels:
        return False
    if "type.ClassOrInterfaceType" in parent.labels:
        return False
    if "type.ClassOrInterfaceType" in node.labels:
        return False
    if "body.ConstructorDeclaration" in parent.labels:
        return False
    if "type.TypeParameter" in parent.labels:
        return False
    return True

def get_package(source, root_node):
    for node in root_node.children:
        if 'PackageDeclaration' in node.labels:
            package_name = node.children[0].get_snippet(source).replace("\t", "").replace(" ", "").replace("\n", "")
            return package_name
    return None

def get_imports(source, root_node):
    imports = []
    for node in root_node.children:
        if 'ImportDeclaration' in node.labels:
            import_str = node.children[0].get_snippet(source).replace("\t", "").replace(" ", "").replace("\n", "")
            imports += [import_str]
    return imports


def get_classes(root_node):
    class_labels = set(['body.ClassOrInterfaceDeclaration', 'body.EnumDeclaration',
                        'body.ClassDeclaration', 'body.InterfaceDeclaration', 'body.AnnotationDeclaration'])
    classes = []
    for node in all_nodes(root_node):
        if node.labels & class_labels:
            classes += [node]
    return classes


def collect_java_sources(path):
    import os
    for dir, _, fnames in os.walk(os.path.expanduser(path)):
        for fname in fnames:
            if fname.endswith(".java"):
                yield os.path.abspath(os.path.join(dir, fname))





#TODO: avoid getting all output at once
def build_asts(source_fnames):
    import os
    from subprocess import Popen, PIPE
    script_path = os.path.dirname(os.path.realpath(__file__))
    parse_pipe_location = os.path.join(script_path, "..", "javaparser", "parse_pipeline.sh")
    process = Popen(['sh', parse_pipe_location], stdout=PIPE, stdin=PIPE, stderr=PIPE)
    output = process.communicate(input="\n".join(source_fnames))[0]
    for line in output.strip().split("\n"):
        markup_serialized = line.strip().split("\t")
        fname = markup_serialized.pop(0)
        if line.endswith("<CUT>"):
          yield (fname, None)
          continue
        source = open(fname).read()
        line_offsets = get_line_offsets(source)
        markup = {}
        for line in markup_serialized:
            delim = line.find("=")
            coords, label = line[:delim], line[delim + 1:].rstrip()
            sline, scol, eline, ecol = [int(item) for item in coords.split(":")]
            start = line_offsets[sline - 1] + scol - 1
            end = line_offsets[eline - 1] + ecol
            markup.setdefault((start, end), set()).add(label)
        root = markup2tree(markup, source)
        yield (fname, root)


def inside_type_bracets(position, snippet):
    bracets_count = 0
    for index in xrange(position):
        if snippet[index] == "<":
            bracets_count += 1
        elif snippet[index] == ">":
            bracets_count -= 1
    return bracets_count > 0

def parse_method_declaration(class_node, method_node, source):
    elems = [elem for elem in method_node.children if not set(['expr.MarkerAnnotationExpr', 'expr.SingleMemberAnnotationExpr',
                                                            'expr.NormalAnnotationExpr', 'comments.JavadocComment',
                                                            'comments.LineComment', 'comments.BlockComment']) & elem.labels]
    return_type = None
    snippet = method_node.get_snippet(source)
    output_type_params = []
    for elem_index in xrange(len(elems)):
        elem = elems[elem_index]
        if inside_type_bracets(elem.start - method_node.start, snippet):
            output_type_params += [elem]
        else:
            elems = elems[elem_index:]
            break
    if [1 for label in elems[0].labels if 'type.' in label]:
        if "body.ConstructorDeclaration" in method_node.labels:
            raise Exception("return type in constructor declaration", method_node.get_snippet(source))
        return_type = elems[0]
        elems = elems[1:]
    elif not "body.ConstructorDeclaration" in method_node.labels:
        raise Exception("no return type in method declaration", method_node.get_snippet(source))

    if len(elems[0].labels) != 1 or not "expr.SimpleName" in elems[0].labels:
        #print elems[0].labels, "||", elems[0].get_snippet(source)
        #print method_node.get_snippet(source)[:100].replace("\n", " ")
        #print "--"
        raise Exception("type outside return declaration", method_node.get_snippet(source))
    method_name = elems[0]
    elems = elems[1:]
    params = []
    from find_var_defs import get_var_decs_from_var_def
    for elem in elems:
        if not 'body.Parameter' in elem.labels:
            break
        params += get_var_decs_from_var_def(elem, class_node, source)
    return (return_type, method_name, params, output_type_params)

