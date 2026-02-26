# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: archive-tools
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: gl10top10validator
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
# MNGA-002: Import organization needs review
import json
import glob
import sys
import os
# Read index
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
operational_dir = os.path.join(repo_root, "gl", "10-operational")
os.chdir(operational_dir)
try:
    with open(".gl-index.json", encoding='utf-8') as _f:
        index=json.load(_f)
except Exception as e:
    print("Missing .gl-index.json",e); sys.exit(2)
required_sem=index.get("semanticterms_required",[])
required_func=index.get("functionaldimensions_required",[])
files=glob.glob("**/gl1*.json", recursive=True) + glob.glob("**/GL1*.json", recursive=True)
files=list(set(files))
# Normalize
files=[f for f in files if "/.git/" not in f]
missing_files=[]
language_mismatch=[]
format_discrepancy=[]
naming_inconsist=[]
semantic_inconsist=[]
artifact_locations=[]
# Collect semantic and functional terms
artifact_semantic={}
artifact_func={}
for f in files:
    try:
        with open(f, encoding='utf-8') as _f:
            data=json.load(_f)
    except Exception:
        format_discrepancy.append(f); continue
    # Check id prefix (exclude special files like schema and completion markers)
    basename = os.path.basename(f)
    if basename not in ["GL10-schema.json", "GL10TOP10COMPLETE.json"]:
        if not data.get("id","").lower().startswith("gl1"):
            naming_inconsist.append(f)
    # Check language
    lang=data.get("language","")
    if lang and lang not in ["zh-TW","en","zh-CN"]:
        language_mismatch.append(f)
    # Check semantic and functional
    st=[s.lower() for s in data.get("semanticterms",[])]
    fd=[d.lower() for d in data.get("functionaldimensions",[])]
    artifact_semantic[f]=st
    artifact_func[f]=fd
    # Location mismatch: path field vs actual path
    path_field=data.get("path","")
    if path_field and os.path.normpath(path_field) != os.path.normpath(f):
        artifact_locations.append({"file":f,"path_field":path_field})
# Semantic consistency: check presence of required terms across artifacts
# Exclude special files (schema, completion markers) from consistency check
special_files = ["GL10-schema.json", "GL10TOP10COMPLETE.json"]
valid_files = [f for f in files if os.path.basename(f) not in special_files]
total=len(valid_files) if valid_files else 1
match_count=0
for f,terms in artifact_semantic.items():
    if os.path.basename(f) not in special_files:
        if any(req.lower() in terms for req in required_sem):
            match_count+=1
consistency=match_count/total
# Missing directories check
expected_dirs=["sop","risk-control","compliance","metrics","issue-tracking","training","policies","procedures","documentation"]
for d in expected_dirs:
    if not os.path.isdir(d):
        missing_files.append(d)
# Produce report
report={"missingdirectories":missing_files,"formatdiscrepancy":format_discrepancy,"naminginconsistencies":naming_inconsist,"artifactlocationmismatch":artifact_locations,"languageissues":language_mismatch,"semanticconsistency":round(consistency,2)}
print(json.dumps(report))
# Blocking conditions
if missing_files or format_discrepancy or naming_inconsist or consistency < 0.75:
    sys.exit(2)
sys.exit(0)