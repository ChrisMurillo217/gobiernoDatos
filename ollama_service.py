import ollama
from config import OLLAMA_HOST, OLLAMA_MODEL

class OllamaService:
    def __init__(self, host=OLLAMA_HOST, model=OLLAMA_MODEL):
        self.client = ollama.Client(host=host)
        self.model = model

    def generate(self, prompt):
        try:
            response = self.client.generate(model=self.model, prompt=prompt)
            return response['response']
        except Exception as e:
            print(f"[Error] Ollama generation failed: {e}")
            return None

    def chat(self, messages):
        try:
            response = self.client.chat(model=self.model, messages=messages)
            return response['message']['content']
        except Exception as e:
            print(f"[Error] Ollama chat failed: {e}")
            return None

    def check_connection(self):
        try:
            self.client.list()
            return True
        except Exception:
            return False
