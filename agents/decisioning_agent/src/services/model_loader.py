"""
LLM Model Loader
"""

from langchain_groq import ChatGroq

from dotenv import load_dotenv

load_dotenv()

def get_llm(temperature: float = 0.0):
    """
    Centralized LLM loader.

    Allows easy swapping of models.
    """

    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=temperature,
        model_kwargs={
        "response_format": {"type": "json_object"}
    }
    )
    
# llm = get_llm()

# print(llm.invoke("Hello, how are you?"))