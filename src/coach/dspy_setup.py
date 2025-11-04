"""DSPy configuration for Ollama"""
import dspy

def setup_dspy(model: str = "qwen3:8b"):
    """Configure DSPy with Ollama"""
    try:
        lm = dspy.LM(
            f'ollama_chat/{model}',
            api_base='http://localhost:11434',
            api_key=''
        )
        dspy.configure(lm=lm)
        return True
    except Exception as e:
        print(f"Failed to setup DSPy: {e}")
        return False