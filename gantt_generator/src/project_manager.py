import os
import yaml
from typing import List, Dict, Optional
from datetime import datetime


PROJECTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'projects')


def ensure_projects_dir():
    if not os.path.exists(PROJECTS_DIR):
        os.makedirs(PROJECTS_DIR)


def get_project_path(project_name: str) -> str:
    safe_name = project_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
    return os.path.join(PROJECTS_DIR, f'{safe_name}.yaml')


def save_project(project_name: str, input_format: str, input_text: str) -> bool:
    ensure_projects_dir()
    
    project_data = {
        'name': project_name,
        'format': input_format,
        'content': input_text,
        'updated_at': datetime.now().isoformat()
    }
    
    project_path = get_project_path(project_name)
    
    try:
        with open(project_path, 'w', encoding='utf-8') as f:
            yaml.dump(project_data, f, allow_unicode=True, default_flow_style=False)
        return True
    except Exception as e:
        print(f"Error saving project: {e}")
        return False


def load_project(project_name: str) -> Optional[Dict]:
    project_path = get_project_path(project_name)
    
    if not os.path.exists(project_path):
        return None
    
    try:
        with open(project_path, 'r', encoding='utf-8') as f:
            project_data = yaml.safe_load(f)
        return project_data
    except Exception as e:
        print(f"Error loading project: {e}")
        return None


def list_projects() -> List[str]:
    ensure_projects_dir()
    
    projects = []
    for filename in os.listdir(PROJECTS_DIR):
        if filename.endswith('.yaml'):
            project_name = filename[:-5].replace('_', ' ')
            projects.append(project_name)
    
    return sorted(projects)


def delete_project(project_name: str) -> bool:
    project_path = get_project_path(project_name)
    
    if not os.path.exists(project_path):
        return False
    
    try:
        os.remove(project_path)
        return True
    except Exception as e:
        print(f"Error deleting project: {e}")
        return False


def create_default_project() -> str:
    default_name = f"New Project {datetime.now().strftime('%Y%m%d_%H%M%S')}"
    default_content = """任务名 | 开始 | 结束 | 分组 | 状态 | 进度 | 依赖
Task 1 | 2026-06-01 | 2026-06-05 | General | pending | 0 |"""
    
    save_project(default_name, 'Table', default_content)
    return default_name
