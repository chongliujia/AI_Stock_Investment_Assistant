import yaml
import os 

class OrchestratorConfig:
    def __init__(self, settings_file="config/settings.yaml"):
        if not os.path.exists(settings_file):
            self.config = {"llm_provider": "openai"}
        else:
            with open(settings_file, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)

    def get_llm_provider_name(self):
        return self.config.get("llm_provider", "openai")
