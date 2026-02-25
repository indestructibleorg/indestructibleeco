import os, re, sys

# 定義專業術語映射表
MAPPINGS = {
    # 中文替換
    "語義驗證": "Schema 驗證",
    "語義表示": "Spec 定義",
    "語義核心": "Spec 核心",
    "語義折疊": "Spec 聚合",
    "語義一致性": "Spec 一致性",
    "語義失真": "Spec 偏離",
    "語義完整": "Spec 完整",
    "語義": "Spec",
    
    # 英文替換 (精準匹配)
    r"\bSemantic Validation\b": "Schema Validation",
    r"\bSemantic Core\b": "Spec Core",
    r"\bSemantic Folding\b": "Spec Aggregation",
    r"\bSemantic Node\b": "Spec Node",
    r"\bFoldedSemantics\b": "AggregatedSpec",
    r"\bTestFoldedSemantics\b": "TestAggregatedSpec",
    r"\bsemantic-core\b": "spec-core",
    r"\bsemantic-folding\b": "spec-aggregation",
    r"\bsemantic_core\b": "spec_core",
    r"\bsemantic_folding\b": "spec_aggregation",
    r"\bLayer Semantics\b": "Layer Spec",
    r"\bMethod Semantics\b": "Method Spec",
    r"\bDomain Semantics\b": "Domain Spec",
    r"\bCapability Semantics\b": "Capability Spec",
    r"\bResource Semantics\b": "Resource Spec",
    r"\bLabel Semantics\b": "Label Spec",
    r"\bDuplicate Semantics\b": "Duplicate Spec",
}

EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", "venv", ".venv"}
EXCLUDE_FILES = {"TERMINOLOGY_MAPPING.md", "refactor_terminology.py"}

def refactor_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        new_content = content
        for pattern, replacement in MAPPINGS.items():
            new_content = re.sub(pattern, replacement, new_content)
            
        if new_content != content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return False

def main():
    count = 0
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file in EXCLUDE_FILES:
                continue
            
            filepath = os.path.join(root, file)
            if refactor_file(filepath):
                print(f"Refactored: {filepath}")
                count += 1
    
    print(f"Total files refactored: {count}")

if __name__ == "__main__":
    main()
