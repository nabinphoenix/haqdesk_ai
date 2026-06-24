import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.llm_gateway import LLMGateway, LLMGatewayError
from app.core.config import settings
from app.core.preflight import run_preflight
from app.prompts.customer_reply_prompt import build_customer_reply_messages
from app.services.rag_service import rag_service

# 1. LLM gateway uses primary model when it succeeds.
@pytest.mark.asyncio
async def test_llm_gateway_primary_success():
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = "This is a reply from the primary model."
    
    with patch("litellm.acompletion", return_value=mock_response) as mock_acompletion:
        gateway = LLMGateway()
        result = await gateway.generate([{"role": "user", "content": "hello"}])
        
        assert result.content == "This is a reply from the primary model."
        assert result.model == settings.LLM_PRIMARY_MODEL
        assert result.fallback_used is False
        mock_acompletion.assert_called_once()

# 2. LLM gateway falls back to second model on rate-limit error.
@pytest.mark.asyncio
async def test_llm_gateway_fallback_on_rate_limit():
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = "This is a reply from the fallback model."
    
    class MockRateLimitError(Exception):
        status_code = 429
        def __str__(self):
            return "Rate limit exceeded (429)"

    with patch("litellm.acompletion") as mock_acompletion:
        mock_acompletion.side_effect = [
            MockRateLimitError(),
            mock_response
        ]
        
        with patch.object(settings, "LLM_FALLBACK_ENABLED", True), \
             patch.object(settings, "LLM_FALLBACK_MODELS", "gemini/gemini-2.0-flash"), \
             patch.object(settings, "LLM_MAX_RETRIES_PER_MODEL", 0), \
             patch.dict("os.environ", {"GEMINI_API_KEY": "dummy_key", "GROQ_API_KEY": "dummy_key"}):
             
            gateway = LLMGateway()
            result = await gateway.generate([{"role": "user", "content": "hello"}])
            
            assert result.content == "This is a reply from the fallback model."
            assert result.model == "gemini/gemini-2.0-flash"
            assert result.fallback_used is True
            assert mock_acompletion.call_count == 2

# 3. LLM gateway raises controlled LLMGatewayError when all providers fail.
@pytest.mark.asyncio
async def test_llm_gateway_all_fail_raises_error():
    with patch("litellm.acompletion", side_effect=Exception("API limit exceeded")) as mock_acompletion:
        with patch.object(settings, "LLM_FALLBACK_ENABLED", True), \
             patch.object(settings, "LLM_FALLBACK_MODELS", "gemini/gemini-2.0-flash"), \
             patch.object(settings, "LLM_MAX_RETRIES_PER_MODEL", 0), \
             patch.dict("os.environ", {"GEMINI_API_KEY": "dummy_key", "GROQ_API_KEY": "dummy_key"}):
            
            gateway = LLMGateway()
            with pytest.raises(LLMGatewayError) as exc_info:
                await gateway.generate([{"role": "user", "content": "hello"}])
            
            assert "All LLM models failed" in str(exc_info.value)
            assert mock_acompletion.call_count == 2

# 4. Missing optional fallback API key does not crash startup.
def test_missing_optional_key_no_crash():
    from app.core.config import Settings
    s = Settings(
        DATABASE_URL="postgresql://user:pass@localhost/db",
        SECRET_KEY="secret",
        GROQ_API_KEY=None,
        GEMINI_API_KEY=None
    )
    assert s.GROQ_API_KEY is None

# 5. RAG retrieval remains filtered by business_id.
def test_rag_retrieval_filtered_by_business_id():
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchall.return_value = []
    
    with patch("app.services.rag_service._get_embeddings") as mock_embeddings:
        mock_emb_inst = MagicMock()
        mock_emb_inst.embed_query.return_value = [0.1] * 384
        mock_embeddings.return_value = mock_emb_inst
        
        rag_service._retrieve_chunks(question="hello", business_id=42, db=mock_db)
        
        mock_db.execute.assert_called_once()
        args, kwargs = mock_db.execute.call_args
        assert args[1]["biz_id"] == 42

# 6. Prompt builder includes customer message and retrieved context.
def test_prompt_builder_structure():
    chunks = [{"content": "We sell organic apples."}]
    messages = build_customer_reply_messages(
        customer_message="Do you sell apples?",
        context_chunks=chunks,
        sentiment="neutral",
        language="english"
    )
    
    system_prompt = messages[0]["content"]
    user_prompt = messages[1]["content"]
    
    assert "organic apples" in system_prompt
    assert "Do you sell apples?" in user_prompt

# 7. Prompt builder warns or limits unsupported/hallucinated answer behavior.
def test_prompt_builder_warnings():
    chunks = [{"content": "We sell organic apples."}]
    messages = build_customer_reply_messages(
        customer_message="Do you sell apples?",
        context_chunks=chunks,
        sentiment="neutral",
        language="english"
    )
    
    system_prompt = messages[0]["content"]
    assert "hallucinate" in system_prompt or "unsupported" in system_prompt.lower()

# 8. Draft service returns fallback/manual-review draft if LLM gateway fails.
@pytest.mark.asyncio
async def test_rag_query_fallback_on_llm_failure():
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchall.return_value = [
        MagicMock(id=1, content="Organic apples context", document_id=1, similarity=0.9)
    ]
    
    mock_doc = MagicMock()
    mock_doc.filename = "apples.txt"
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_doc]
    
    with patch("app.services.rag_service._get_embeddings") as mock_embeddings, \
         patch("app.services.llm_gateway.llm_gateway.generate", side_effect=LLMGatewayError("Gateway Error")):
        
        mock_emb_inst = MagicMock()
        mock_emb_inst.embed_query.return_value = [0.1] * 384
        mock_embeddings.return_value = mock_emb_inst
        
        res = await rag_service.query(
            question="Do you sell apples?",
            business_id=1,
            db=mock_db,
            confidence_threshold=0.3
        )
        
        assert res is not None
        assert "AI draft could not be generated at this time" in res["answer"]

# 9. Preflight does not expose secret values.
def test_preflight_does_not_expose_secrets():
    with patch("app.core.preflight.check_database", return_value=True), \
         patch("app.core.preflight.check_pgvector", return_value=True), \
         patch("app.core.preflight.check_embedding_model", return_value=True), \
         patch("app.core.preflight.check_sentiment_model", return_value=True):
          
         res = run_preflight()
         
         assert res["ok"] is True
         assert isinstance(res["llm"]["primary_key_set"], bool)
         for fb in res["llm"]["fallback_models"]:
             assert isinstance(fb["key_set"], bool)
             assert "key" not in fb

# 10. LLM gateway retries the same model on retryable error.
@pytest.mark.asyncio
async def test_llm_gateway_retries_on_retryable_error():
    mock_success = AsyncMock()
    mock_success.choices = [AsyncMock()]
    mock_success.choices[0].message.content = "Success response after retries."
    
    class MockRateLimitError(Exception):
        status_code = 429
        def __str__(self):
            return "Rate limit exceeded (429)"

    with patch("litellm.acompletion") as mock_acompletion, \
         patch("asyncio.sleep", return_value=None) as mock_sleep:
        
        mock_acompletion.side_effect = [
            MockRateLimitError(),
            MockRateLimitError(),
            mock_success
        ]
        
        with patch.object(settings, "LLM_MAX_RETRIES_PER_MODEL", 2), \
             patch.object(settings, "LLM_FALLBACK_ENABLED", False), \
             patch.dict("os.environ", {"GROQ_API_KEY": "dummy_key"}):
             
            gateway = LLMGateway()
            result = await gateway.generate([{"role": "user", "content": "hello"}])
            
            assert result.content == "Success response after retries."
            assert result.model == settings.LLM_PRIMARY_MODEL
            assert result.attempts == 3
            assert mock_acompletion.call_count == 3
            assert mock_sleep.call_count == 2
            # Check sleep durations: 2^1 = 2, 2^2 = 4 (both min-capped at 5)
            mock_sleep.assert_any_call(2)
            mock_sleep.assert_any_call(4)

# 11. LLM gateway falls back after retry attempts are exhausted.
@pytest.mark.asyncio
async def test_llm_gateway_fallback_after_retries_exhausted():
    mock_fallback_success = AsyncMock()
    mock_fallback_success.choices = [AsyncMock()]
    mock_fallback_success.choices[0].message.content = "Fallback success response."
    
    class MockRateLimitError(Exception):
        status_code = 429
        def __str__(self):
            return "Rate limit exceeded (429)"

    with patch("litellm.acompletion") as mock_acompletion, \
         patch("asyncio.sleep", return_value=None) as mock_sleep:
        
        # Primary fails twice (1 try, 1 retry), then Fallback succeeds
        mock_acompletion.side_effect = [
            MockRateLimitError(),
            MockRateLimitError(),
            mock_fallback_success
        ]
        
        with patch.object(settings, "LLM_FALLBACK_ENABLED", True), \
             patch.object(settings, "LLM_FALLBACK_MODELS", "gemini/gemini-2.0-flash"), \
             patch.object(settings, "LLM_MAX_RETRIES_PER_MODEL", 1), \
             patch.dict("os.environ", {"GEMINI_API_KEY": "dummy_key", "GROQ_API_KEY": "dummy_key"}):
             
            gateway = LLMGateway()
            result = await gateway.generate([{"role": "user", "content": "hello"}])
            
            assert result.content == "Fallback success response."
            assert result.model == "gemini/gemini-2.0-flash"
            assert result.fallback_used is True
            assert result.attempts == 3
            assert mock_acompletion.call_count == 3
            assert mock_sleep.call_count == 1
            mock_sleep.assert_called_with(2)

# 12. Empty LLM response raises/handles controlled failure.
@pytest.mark.asyncio
async def test_llm_gateway_empty_response_raises_error():
    mock_empty = AsyncMock()
    mock_empty.choices = [AsyncMock()]
    mock_empty.choices[0].message.content = "   " # empty/blank string
    
    with patch("litellm.acompletion", return_value=mock_empty) as mock_acompletion, \
         patch("asyncio.sleep", return_value=None) as mock_sleep:
         
        with patch.object(settings, "LLM_MAX_RETRIES_PER_MODEL", 1), \
             patch.object(settings, "LLM_FALLBACK_ENABLED", False), \
             patch.dict("os.environ", {"GROQ_API_KEY": "dummy_key"}):
             
            gateway = LLMGateway()
            with pytest.raises(LLMGatewayError) as exc_info:
                await gateway.generate([{"role": "user", "content": "hello"}])
                
            assert "All LLM models failed" in str(exc_info.value)
            # Try + 1 retry = 2 calls
            assert mock_acompletion.call_count == 2
            assert mock_sleep.call_count == 1

# 13. Prompt builder contains no mojibake and includes clean Nepali/Romanized Nepali instructions.
def test_prompt_builder_nepali_instructions_no_mojibake():
    # 1. Nepali Devanagari check
    messages_nepali = build_customer_reply_messages(
        customer_message="नमस्ते",
        context_chunks=[{"content": "केही सन्दर्भ"}],
        language="nepali"
    )
    sys_content_nepali = messages_nepali[0]["content"]
    assert "Reply in Nepali using Devanagari script only." in sys_content_nepali
    # Make sure old raw Devanagari Unicode string is NOT present
    assert "देवनागरी" not in sys_content_nepali

    # 2. Romanized Nepali check
    messages_roman = build_customer_reply_messages(
        customer_message="k xa khabar",
        context_chunks=[{"content": "sandarbha"}],
        language="romanized_nepali"
    )
    sys_content_roman = messages_roman[0]["content"]
    assert "Reply in casual romanized Nepali matching the customer's tone. Do not use Devanagari script." in sys_content_roman
    assert "देवनागरी" not in sys_content_roman
