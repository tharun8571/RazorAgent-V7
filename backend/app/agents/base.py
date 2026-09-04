from typing import Type, TypeVar, List, Dict, Any, Optional
from pydantic import BaseModel
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from app.core.llm import get_structured_llm, get_llm
from app.core.logging import logger
from app.core.security import sanitize_for_llm
from app.core.exceptions import LLMUnavailableError, LLMStructuredOutputError
from app.core.config import settings

T = TypeVar("T", bound=BaseModel)


class BaseAgent:
    def __init__(self, agent_name: str, role_description: str):
        self.agent_name = agent_name
        self.role_description = role_description

    async def invoke_structured(
        self,
        schema: Type[T],
        messages: List[BaseMessage],
        request_id: Optional[str] = None,
        payment_id: Optional[str] = None,
        extra_tags: Optional[List[str]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> T:
        """
        Executes an LLM call via Groq with structured Pydantic output.
        Attaches LangSmith tracing tags and metadata without exposing secrets.
        """
        tags = [
            "razoragent-v7",
            f"agent:{self.agent_name}",
            f"env:{settings.ENVIRONMENT}",
        ]
        if extra_tags:
            tags.extend(extra_tags)

        metadata: Dict[str, Any] = {
            "agent_name": self.agent_name,
            "request_id": request_id,
            "payment_id": payment_id,
            "model": settings.GROQ_MODEL,
        }
        if extra_metadata:
            metadata.update(sanitize_for_llm(extra_metadata))

        config = {
            "run_name": f"{self.agent_name}_reasoning",
            "tags": tags,
            "metadata": metadata,
        }

        try:
            structured_llm = get_structured_llm(schema)
            # Invoke structured reasoning asynchronously
            result = await structured_llm.ainvoke(messages, config=config)
            if not isinstance(result, schema):
                # In some versions structured_llm may return dict or object
                if isinstance(result, dict):
                    result = schema.model_validate(result)
                else:
                    raise LLMStructuredOutputError(f"Output is not of expected type {schema.__name__}")
            return result
        except LLMStructuredOutputError:
            raise
        except Exception as e:
            logger.error(
                f"Groq LLM invocation failed in {self.agent_name} for request {request_id}: {str(e)}",
                extra={"agent": self.agent_name, "request_id": request_id, "error": str(e)}
            )
            # Crucial: Raise explicit LLM failure so infrastructure handles escalation
            raise LLMUnavailableError(f"LLM failure in {self.agent_name}: {str(e)}")
