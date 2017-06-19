#LogAn
 
##Usage
 
###Construction of templates
 
Btw: you can find templates built for Hadoop 2.3 in the directory ‘samples’
 
You will need a folder with all source files (Hadoop, Spark, Zookeeper, etc. depending on your needs). Just download related sources, unpack them and put under one directory. The script will iterate over all subfolders and collect java files.
 
####2 stages:
 
1) Index construction:
 
python logan/src/indexing.py “root_folder_with_all_sources” “folder4indices”
 
It will create two files in the folder for indices:
 
markup.db - db for ASTs built on to of the source files (Notice: abstract syntax tree consume few times more space than the original source file)
 
source_index.b - composite of various indices that are necessary for expanding log expressions.
 
2) extraction of log templates
 
python extract_log_templates.py “folder4indices” “output filename or -”
 
Output filename - where to put extracted templates (if you put “-” then it will write templates to stdout)
 
Notice: it is normal that the tool might extract many templates per one log call expression, since frequently there are several ways of how to expand or replace values of variable and expressions.
 
###Parsing log messages
 
python logan/src/match_log_lines.py <path to bz2-compressed templates file> <input filename or - > <output filename or - >
 
Notice: the script expects bz2-compressed file with templates as a first parameter. You can find templates built for Hadoop 2.3 in the directory ‘samples’
 
Input fname or stdin - log messages, one message per line. You can find a sample in the directory “samples”.
Output fname or stdout - where to matched and parsed log messages.
 
For every log line it produces a json of the following structure:
 
{
    "matched_templates": [  // <---- list of matched templates
        {
            "matched": [  // <---- (placeholder, value) list of matched values
                [
                    [
                        "org.apache.hadoop.hdfs.protocol.ExtendedBlock:::block.getLocalBlock()"  // <---- placeholder
                    ], 
                    "blk_1076177292_2505416" // <---- matched value
                ], 
                [
                    [
                        "java.io.File:::blockFile"
                    ], 
                    "/mnt/dfs/dn/current/BP-1688309351-134.21.73.230-1398969552123/current/finalized/subdir37/subdir41/blk_1076177292"
                ]
            ], 
             "logline": "LOG.info(\"Scheduling \" + block.getLocalBlock()         + \" file \" + blockFile + \" for deletion\")\n",   // <--- actual expression that generates the log line
              "templsrc": "/home/arslan/src/provenance/hadoop/hadoop-hdfs-project/hadoop- hdfs/src/main/java/org/apache/hadoop/hdfs/server/datanode/fsdataset/impl/FsDatasetAsyncDiskService.java" // <--- source file where the log line expression defined
        }
    ], 
    "message": {   // <--- meta data about the original log line
        "epoch": 1455551661.349,   // <---timestamp
        "level": "INFO",   // <---level
        "source": "org.apache.hadoop.hdfs.server.datanode.fsdataset.impl.FsDatasetAsyncDiskService", //  <----- source
        "text": "Scheduling blk_1076177292_2505416 file /mnt/dfs/dn/current/BP-1688309351-134.21.73.230-1398969552123/current/finalized/subdir37/subdir41/blk_1076177292 for deletion"   //  <---- text
    }
}
 
 
 
