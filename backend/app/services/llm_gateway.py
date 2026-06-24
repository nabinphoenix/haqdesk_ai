import os
import time
import logging
import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import litellm
from app.core.config import settings

logger = logging.getLogger("uvicorn")

class LLMGatewayError(Exception):
    pass

class LLMProviderResult(BaseModel):
    model: str
    provider: Optional[str] = None
    content: str
    fallback_used: bool
    attempts: int
    latency_ms: float

def is_retryable_llm_error(exc: Exception) -> bool:
    """
    Detect retryable errors: rate limits, timeouts, temporary outages, empty responses.
    """
    # 1. If exception has status_code
    if hasattr(exc, "status_code"):
        if exc.status_code in [429, 502, 503, 504]:
            return True

    # 2. Check exception class name
    exc_type_name = type(exc).__name__.lower()
    if "ratelimit" in exc_type_name or "timeout" in exc_type_name:
        return True

    # 3. Check message string
    exc_str = str(exc).lower()
    retryable_keywords = [
        "rate limit", "rate_limit", "429", "quota", "resource exhausted", "resource_exhausted",
        "timeout", "timed out", "overloaded", "service unavailable", "service_unavailable",
        "connection reset", "connection_reset", "temporary unavailable", "temporary_unavailable",
        "tpm limit", "rpm limit", "503", "504", "502", "bad gateway",
        "empty response", "empty llm response"
    ]
    return any(kw in exc_str for kw in retryable_keywords)

class LLMGateway:
    def __init__(self):
        # Propagate config keys to os.environ for LiteLLM's internal use
        for key in ["GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
            val = getattr(settings, key, None)
            if val and key not in os.environ:
                os.environ[key] = val
        
        # Disable litellm telemetry
        litellm.telemetry = False

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 500,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LLMProviderResult:
        # Determine model list starting with primary
        models_to_try = [settings.LLM_PRIMARY_MODEL]
        
        if settings.LLM_FALLBACK_ENABLED and settings.LLM_FALLBACK_MODELS:
            fallbacks = [m.strip() for m in settings.LLM_FALLBACK_MODELS.split(",") if m.strip()]
            models_to_try.extend(fallbacks)
            
        attempts = 0
        start_time = time.time()
        
        for idx, model in enumerate(models_to_try):
            provider = model.split("/")[0] if "/" in model else None
            
            # Check if key is available for this model's provider
            key_name = f"{provider.upper()}_API_KEY" if provider else None
            if key_name and not os.environ.get(key_name) and not getattr(settings, key_name, None):
                logger.warning(f"⚠️ Skipping model {model} because {key_name} is not configured.")
                if idx == 0 and not settings.LLM_FALLBACK_ENABLED:
                    raise LLMGatewayError(f"Primary model {model} API key {key_name} is not configured and fallback is disabled.")
                continue
                
            retry_count = settings.LLM_MAX_RETRIES_PER_MODEL
            
            for model_attempt in range(retry_count + 1):
                attempts += 1
                logger.info(f"LLM draft attempt {attempts} (model attempt {model_attempt + 1}/{retry_count + 1}): using model={model}")
                
                try:
                    # Call LiteLLM acompletion
                    response = await litellm.acompletion(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        timeout=settings.LLM_TIMEOUT_SECONDS,
                    )
                    
                    content = response.choices[0].message.content
                    if not content or not content.strip():
                        raise ValueError("LLM returned empty response")
                        
                    content = content.strip()
                    
                    latency_ms = (time.time() - start_time) * 1000
                    fallback_used = idx > 0
                    
                    logger.info(
                        f"LLM draft generated model={model} fallback_used={fallback_used} "
                        f"latency_ms={latency_ms:.1f} attempts={attempts}"
                    )
                    
                    return LLMProviderResult(
                        model=model,
                        provider=provider,
                        content=content,
                        fallback_used=fallback_used,
                        attempts=attempts,
                        latency_ms=latency_ms
                    )
                    
                except Exception as e:
                    latency_ms = (time.time() - start_time) * 1000
                    retryable = is_retryable_llm_error(e)
                    
                    logger.warning(
                        f"LLM provider failed model={model} attempt {model_attempt + 1} "
                        f"reason={str(e)[:150]} retryable={retryable} latency_ms={latency_ms:.1f}"
                    )
                    
                    # If this failure can be retried and we have attempts left
                    if model_attempt < retry_count and retryable:
                        attempt_sleep = model_attempt + 1
                        sleep_duration = min(2 ** attempt_sleep, 5)
                        logger.info(f"LLM retrying model {model} in {sleep_duration}s...")
                        await asyncio.sleep(sleep_duration)
                        continue
                    
                    # Otherwise, retries for this model are exhausted or it is non-retryable
                    if not retryable and not settings.LLM_FALLBACK_ENABLED:
                        raise LLMGatewayError(f"LLM generation failed on non-retryable error: {e}") from e
                        
                    # If this is the last model in the list, raise the final error
                    if idx == len(models_to_try) - 1:
                        raise LLMGatewayError(f"All LLM models failed. Last error: {e}") from e
                        
                    # Otherwise, continue to the fallback model by breaking the retry loop
                    logger.info(f"LLM falling back to next provider after attempts for model {model} failed. Error: {e}")
                    break
                    
        raise LLMGatewayError("No LLM models were executed successfully.")

# Singleton instance
llm_gateway = LLMGateway()
