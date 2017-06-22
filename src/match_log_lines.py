import sys
import json


def tokenize(text):
    import re
    return re.findall("[a-zA-Z0-9]+", text)

def upload_templates(bz2_fname):
    import bz2
    import json
    templates = []
    by_longest_chunk = {}
    for line in bz2.BZ2File(bz2_fname):
        if not line:
            break
        template_json = json.loads(line)
        if not template_json["chunks"]:
            continue
        if "merge conseq strings":
            shortened = [template_json["chunks"][0]]
            for chunk_type, placeholder_type, placeholder in template_json["chunks"][1:]:
                if chunk_type == "SC" and shortened[-1][0] == "SC":
                    shortened[-1] = ["SC", shortened[-1][1], shortened[-1][2] + placeholder]
                else:
                    shortened.append([chunk_type, placeholder_type, placeholder])
            template_json["chunks"] = shortened

        for chunk_index in xrange(len(template_json["chunks"])):
            template_json["chunks"][chunk_index][-1] = \
                template_json["chunks"][chunk_index][-1].replace("<TAB>", "\t").replace("<BR>", "\n")

        static_length = 0
        for chunk_type, placeholder_type, placeholder in template_json["chunks"]:
            if chunk_type == "SC":
                static_length += len(placeholder)
        if static_length < 10:
            continue
        longest_chunk = ""
        for chunk_type, placeholder_type, placeholder in template_json["chunks"]:
            if chunk_type == "SC":
                for token in tokenize(placeholder):
                    if len(token) > len(longest_chunk):
                        longest_chunk = token
        by_longest_chunk.setdefault(longest_chunk, []).append(len(templates))
        templates += [template_json]
    return templates, by_longest_chunk


def decompose_raw_log_message(message):
    timestamp_end = message.find(" ", message.find(" ") + 1)
    message_level_end = message.find(" ", timestamp_end + 1)
    source_end = message.find(": ", message_level_end + 1)
    timestamp, msg_level, msg_source, msg_text = (message[:timestamp_end],
                                                  message[timestamp_end + 1:message_level_end],
                                                  message[message_level_end + 1:source_end],
                                                  message[source_end + 1:].strip()
                                                  )
    try:
      timestamp1, millisec = timestamp.split(",")
      timestamp = timestamp1
    except:
      #no millisecs
      millisec = 0.0
      pass
    timestamp = timestamp.replace("-", ":").replace("/", ":")
    from datetime import datetime
    import time
    try:
      epoch = time.mktime(datetime.strptime(timestamp, '%Y:%m:%d %H:%M:%S').timetuple()) + float(millisec) / 1000.0
    except Exception as e:
      epoch = 0
    if not epoch:
      try:
        epoch = time.mktime(datetime.strptime(timestamp, '%y:%m:%d %H:%M:%S').timetuple()) + float(millisec) / 1000.0
      except Exception as e:
        epoch = 0
    if not epoch:
      raise Exception("parsing error", "failed parsing timestamp:" + timestamp)
    message = {"epoch": epoch, "level": msg_level, "source": msg_source, "text":msg_text}
    return message


def find_all_matches(message, templates, templates_index):
    possible_matches = []
    text = message["text"]
    for token in tokenize(text):
        if token in templates_index:
            possible_matches += templates_index[token]
    max_matched_len = -1
    best_matches = []
    for templ_index in possible_matches:
        template_json = templates[templ_index]
        template_package = template_json["package"]
        #pre-filter, works only if the message source was stated as a full class path
        if message["source"].startswith("org.") and not message["source"].startswith(template_package):
            continue
        matched = True
        matched_elements = []
        start = 0
        elements2match = []
        for chunk_type, placeholder_type, placeholder in template_json["chunks"]:
            if chunk_type != "SC":
                elements2match.append(placeholder_type + "::" + placeholder)
                continue
            pos = text.find(placeholder, start)
            if pos < start:
                matched = False
                break
            if len(elements2match) > 0:
                matched_elements += [([elem for elem in elements2match], text[start:pos])]
                elements2match = []
            elif pos > start and start > 0:
                matched = False
                break
            matched_elements += [placeholder]
            start = pos + len(placeholder)
        if matched:
            if elements2match:
                if start < len(text):
                    matched_elements += [([elem for elem in elements2match], text[start:])]
                else:
                    matched = False
            elif start < len(text):
                matched = False
        if matched:
            matched_length = sum(len(matched_elem) for matched_elem in matched_elements if type(matched_elem) == str)
            if matched_length > max_matched_len:
                max_matched_len = matched_length
                best_matches = []
            if matched_length == max_matched_len:
                only_replacements = [elem for elem in matched_elements if type(elem) != str]
                best_matches.append( (templ_index, only_replacements) )
    return best_matches



if __name__ == "__main__":
    try:
        bz2_templates_fname, input, output = sys.argv[1:]
        input_stream = input == "-" and sys.stdin or open(input, "r")
        output_stream = output == "-" and sys.stdout or open(output, "w")
    except Exception as e:
        print "usage: python match_log_lines.py <path to archived templates.json> <input filename or - > <output filename or - >"
        exit()
    sys.stderr.write("loading templates.\n")
    sys.stderr.flush()
    templates, index = upload_templates(bz2_templates_fname)
    sys.stderr.write("uploaded %d templates.\n" % (len(templates)))
    sys.stderr.flush()
    matched = 0
    processed = 0
    for message_line in input_stream:
        try:
          message = decompose_raw_log_message(message_line)
        except:
          continue
        matched_templates = find_all_matches(message, templates, index)
        all_matches = []
        for templ_index, matched_elements in matched_templates:
            all_matches.append(({"templsrc": templates[templ_index]["source"],
                                 "logline:": templates[templ_index]["logcall"],
                                 "matched": matched_elements}))
        matches = {"message": message, "matched_templates": all_matches}
        output_stream.write(json.dumps(matches) + "\n")

        processed += 1
        if all_matches:
            matched += 1
        if processed % 10000 == 0:
            sys.stderr.write("..processed %d, matched %d\n" % (processed, matched))



