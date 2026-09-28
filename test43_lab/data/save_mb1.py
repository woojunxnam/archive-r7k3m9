"""decode auto-saved Drive download results (JSON {content(base64), title}) into data/mb1/<title>; exact bytes; source removed."""
import base64, glob, json, os, sys
D = "/root/.claude/projects/-home-user-archive-r7k3m9/97e20997-4bf8-5cb9-8419-c622ea23a2b5/tool-results"
paths = sys.argv[1:] or glob.glob(os.path.join(D, "mcp-Google_Drive-download_file_content-*.txt"))
for p in paths:
    try:
        d = json.load(open(p)); t = d["title"]
        if ".mb1.part" not in t:
            continue
        b = base64.b64decode(d["content"]); open(os.path.join("/home/user/lab/data/mb1", t), "wb").write(b); os.remove(p); print(t, len(b))
    except Exception as e:
        print("ERR", p, e)
