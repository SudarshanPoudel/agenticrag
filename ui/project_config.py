from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
import os
import json

PROJECTS_DIR = "ui/projects"

@dataclass
class LLMConfig:
    provider: str = "gemini"
    model: str = "gemini-2.0-pro"
    temperature: float = 0.7
    api_key: Optional[str] = None

@dataclass
class StoreFlags:
    enable_text_store: bool = True
    enable_table_store: bool = True
    enable_external_db_store: bool = False

@dataclass
class RetrieverConfig:
    enable_vector_retriever: bool = True
    vector_top_k: int = 5
    enable_table_retriever: bool = True
    enable_sql_retriever: bool = False

@dataclass
class TaskConfig:
    enable_qa_task: bool = True
    enable_chart_task: bool = True

@dataclass
class ProjectConfig:
    project_name: str = "default"
    persist_dir: str = "ui/.project_name_data"
    meta_conn_url: str = ""
    llm: LLMConfig = field(default_factory=LLMConfig)
    stores: StoreFlags = field(default_factory=StoreFlags)
    retrievers: RetrieverConfig = field(default_factory=RetrieverConfig)
    tasks: TaskConfig = field(default_factory=TaskConfig)
    # optional extra per-component settings
    extras: Dict[str, Any] = field(default_factory=dict)

def ensure_projects_dir():
    os.makedirs(PROJECTS_DIR, exist_ok=True)

def project_json_path(project_name: str) -> str:
    ensure_projects_dir()
    safe = project_name.strip().replace(" ", "_")
    return os.path.join(PROJECTS_DIR, f"{safe}.json")

def save_project_config(cfg: ProjectConfig):
    ensure_projects_dir()
    path = project_json_path(cfg.project_name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(cfg), f, indent=2)

def load_project_config(project_name: str) -> Optional[ProjectConfig]:
    path = project_json_path(project_name)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    # rebuild nested structures
    llm = LLMConfig(**raw.get("llm", {}))
    stores = StoreFlags(**raw.get("stores", {}))
    retrievers = RetrieverConfig(**raw.get("retrievers", {}))
    tasks = TaskConfig(**raw.get("tasks", {}))
    cfg = ProjectConfig(
        project_name=raw.get("project_name", "default"),
        persist_dir=raw.get("persist_dir", "ui/.project_name_data"),
        meta_conn_url=raw.get("meta_conn_url", ""),
        llm=llm,
        stores=stores,
        retrievers=retrievers,
        tasks=tasks,
        extras=raw.get("extras", {}),
    )
    return cfg

def list_projects() -> List[str]:
    ensure_projects_dir()
    names = []
    for f in os.listdir(PROJECTS_DIR):
        if f.endswith(".json"):
            names.append(os.path.splitext(f)[0])
    return sorted(names)

def delete_project(project_name: str) -> bool:
    # deletes JSON and persistent dir
    import shutil
    cfg = load_project_config(project_name)
    path = project_json_path(project_name)
    ok = True
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            ok = False
    if cfg and os.path.isdir(cfg.persist_dir):
        try:
            shutil.rmtree(cfg.persist_dir)
        except Exception:
            ok = False
    return ok
