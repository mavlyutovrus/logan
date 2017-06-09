import com.github.javaparser.JavaParser;
import com.github.javaparser.ParseException;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.Node;

import java.io.*;
import java.util.*;

/**
 * Created by arslan on 1/30/17.
 */
public class PrintAST {
    static BufferedWriter Output;
    public static void iter(List<Node> nodes) throws java.io.IOException {
        for (Node node : nodes) {
            int bLine = node.getRange().get().begin.line;
            int bColumn = node.getRange().get().begin.column;
            int eLine = node.getRange().get().end.line;
            int eColumn = node.getRange().get().end.column;
            String coords = String.valueOf(bLine) + ":" + String.valueOf(bColumn) + ":" + String.valueOf(eLine) + ":" + String.valueOf(eColumn) + "=";
            Output.write(coords + node.getClass().toString().split(".ast.")[1] + "\t");
            iter(node.getChildNodes());
        }
    }

    public static void main(String[] args) throws FileNotFoundException, IOException, ParseException {
       BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
       Output = new BufferedWriter(new OutputStreamWriter(System.out));
       String fname;
       while ((fname = reader.readLine()) != null) {
           Output.write(fname + "\t");
           CompilationUnit cu = JavaParser.parse(new FileInputStream(fname));
           iter(cu.getChildNodes());
           Output.write("\n");
           Output.flush();
       }
    }
}
