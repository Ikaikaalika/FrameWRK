from .config import settings
from .services.llm_provider import LLMProvider
from .services.openai_provider import OpenAIProvider
from .services.anthropic_provider import AnthropicProvider
from .services.ollama_provider import OllamaProvider
from .services.embeddings import EmbeddingsService
from .services.vectorstore import VectorStore
from .services.rag_pipeline import RAGPipeline
from .services.ops_service import OpsService
from .services.automation_service import AutomationService

def get_llm_provider() -> LLMProvider:
    if settings.OPENAI_API_KEY:
        return OpenAIProvider(settings.OPENAI_API_KEY)
    if settings.ANTHROPIC_API_KEY:
        return AnthropicProvider(settings.ANTHROPIC_API_KEY)
    return OllamaProvider(base_url=settings.OLLAMA_BASE_URL, model=settings.OLLAMA_MODEL)

def get_embeddings() -> EmbeddingsService:
    return EmbeddingsService(provider=settings.EMBEDDINGS_PROVIDER,
                             model=settings.EMBEDDINGS_MODEL,
                             openai_key=settings.OPENAI_API_KEY,
                             ollama_base=settings.OLLAMA_BASE_URL)

def get_vectorstore() -> VectorStore:
    return VectorStore(url=settings.QDRANT_URL, collection=settings.QDRANT_COLLECTION)

def get_rag_pipeline() -> RAGPipeline:
    return RAGPipeline(embeddings=get_embeddings(), store=get_vectorstore(), llm=get_llm_provider())

def get_ops_service() -> OpsService:
    return OpsService.from_file()

def get_automation_service() -> AutomationService:
    return AutomationService(rag=get_rag_pipeline(), llm=get_llm_provider())
