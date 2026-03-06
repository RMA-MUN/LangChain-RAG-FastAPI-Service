import os

def get_project_root() -> str:
    """
    获取项目根目录
    :return: 项目根目录路径
    """
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_abstract_path(relative_path: str) -> str:
    """
    根据传入的相对路径，获取项目根目录下的抽象路径
    :param relative_path: 相对项目根目录的路径
    :return: 项目根目录的绝对路径
    """
    project_path = get_project_root()
    abstract_path = os.path.join(project_path, relative_path)
    return abstract_path


if __name__ == '__main__':
    print(get_abstract_path('config/.env'))