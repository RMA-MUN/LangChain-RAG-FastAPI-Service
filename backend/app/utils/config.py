from app.utils.config_handler import load_config
from app.utils.path_tool import get_abstract_path

rag_config = load_config(config_path=get_abstract_path('config/rag.yaml'))
chroma_config = load_config(config_path=get_abstract_path('config/chroma.yaml'))
prompt_config = load_config(config_path=get_abstract_path('config/prompt.yaml'))
agent_config = load_config(config_path=get_abstract_path('config/agent.yaml'))

if __name__ == '__main__':

    print(rag_config)
    print(chroma_config)
    print(prompt_config)
    print(agent_config)