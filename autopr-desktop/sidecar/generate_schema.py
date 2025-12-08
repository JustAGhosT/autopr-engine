import json
from codeflow_engine.config.settings import AutoPRSettings

def generate_schema():
    schema = AutoPRSettings.model_json_schema()
    with open("/app/autopr-desktop/src/schema.json", "w") as f:
        json.dump(schema, f, indent=2)

if __name__ == "__main__":
    generate_schema()
