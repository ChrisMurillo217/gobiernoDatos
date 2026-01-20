try:
    import ollama
    OLLAMA_INSTALLED = True
except ImportError:
    OLLAMA_INSTALLED = False

from app.config.settings import OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_ENABLE

class OllamaService:
    def __init__(self, host=OLLAMA_HOST, model=OLLAMA_MODEL):
        self.enabled = OLLAMA_ENABLE and OLLAMA_INSTALLED
        self.client = None
        self.model = model
        
        if self.enabled:
            try:
                self.client = ollama.Client(host=host)
            except Exception as e:
                print(f"[Advertencia] No se pudo inicializar cliente Ollama: {e}")
                self.enabled = False

    def generate(self, prompt):
        if not self.enabled:
            return None
        try:
            response = self.client.generate(model=self.model, prompt=prompt)
            return response['response']
        except Exception as e:
            print(f"[Error] Ollama generation failed: {e}")
            return None

    def chat(self, messages):
        if not self.enabled:
            return None
        try:
            response = self.client.chat(model=self.model, messages=messages)
            return response['message']['content']
        except Exception as e:
            print(f"[Error] Ollama chat failed: {e}")
            return None

    def check_connection(self):
        if not self.enabled:
            return False
        try:
            self.client.list()
            return True
        except Exception:
            return False
