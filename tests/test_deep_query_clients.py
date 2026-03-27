"""Unit tests for DeepQuery and DeepMind AI clients."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from berb.llm.deep_query_client import (
    DeepQueryClient,
    DeepQueryResult,
    DeepMindAIClient,
    DeepMindAIResult,
    create_deepquery_client,
    create_deepmind_ai_client,
)


class TestDeepQueryClient:
    """Test DeepQueryClient class."""
    
    @pytest.mark.asyncio
    async def test_search_success(self):
        """Test successful DeepQuery search."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "CRISPR is a gene editing technology..."
                    }
                }
            ],
            "citations": ["https://example.com/paper1"],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 500,
                "total_tokens": 600,
            },
        }
        
        with patch("httpx.AsyncClient.post", return_value=mock_response):
            client = DeepQueryClient(api_key="test_key")
            result = await client.search("CRISPR gene editing", model="pro")
        
        assert result.content != ""
        assert result.source == "DeepQuery"
        assert len(result.citations) == 1
    
    @pytest.mark.asyncio
    async def test_search_different_models(self):
        """Test search with different models."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "response"}}],
            "citations": [],
            "usage": {},
        }
        
        with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
            client = DeepQueryClient(api_key="test_key")
            
            # Test quick model
            await client.search("test", model="quick")
            call_args = mock_post.call_args[1]["json"]
            assert call_args["model"] == "sonar"
            
            # Test reasoning model
            await client.search("test", model="reasoning")
            call_args = mock_post.call_args[1]["json"]
            assert call_args["model"] == "sonar-reasoning-pro"
    
    @pytest.mark.asyncio
    async def test_literature_review(self):
        """Test literature review functionality."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Comprehensive review..."}}],
            "citations": ["https://paper1.com", "https://paper2.com"],
            "usage": {},
        }
        
        with patch("httpx.AsyncClient.post", return_value=mock_response):
            client = DeepQueryClient(api_key="test_key")
            result = await client.literature_review(
                topic="machine learning",
                focus_areas=["deep learning", "NLP"],
                year_range=(2020, 2024),
            )
        
        assert result.content != ""
        assert len(result.citations) == 2
    
    @pytest.mark.asyncio
    async def test_verify_citation_verified(self):
        """Test citation verification - verified case."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "VERIFIED: This paper exists..."}}],
            "citations": ["https://paper.com"],
            "usage": {},
        }
        
        with patch("httpx.AsyncClient.post", return_value=mock_response):
            client = DeepQueryClient(api_key="test_key")
            result = await client.verify_citation(
                citation_text="Smith et al. (2023). Nature.",
                claimed_finding="CRISPR improves efficiency",
            )
        
        assert result["status"] == "verified"
    
    @pytest.mark.asyncio
    async def test_verify_citation_inaccurate(self):
        """Test citation verification - inaccurate case."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "INACCURATE: Paper says something different..."}}],
            "citations": [],
            "usage": {},
        }
        
        with patch("httpx.AsyncClient.post", return_value=mock_response):
            client = DeepQueryClient(api_key="test_key")
            result = await client.verify_citation(
                citation_text="Smith et al. (2023).",
                claimed_finding="Wrong claim",
            )
        
        assert result["status"] == "inaccurate"
    
    def test_get_model_info(self):
        """Test getting model information."""
        client = DeepQueryClient(api_key="test_key")
        info = client.get_model_info()
        
        assert info["provider"] == "DeepQuery (Perplexity)"
        assert "models" in info
        assert "sonar" in info["models"]
        assert "sonar-pro" in info["models"]
        assert "sonar-deep-research" in info["models"]


class TestDeepMindAIClient:
    """Test DeepMindAIClient class."""
    
    @pytest.mark.asyncio
    async def test_chat_success(self):
        """Test successful chat completion."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "chat_123",
            "created": 1234567890,
            "choices": [
                {
                    "message": {"content": "Response from Grok"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 500,
                "total_tokens": 600,
            },
        }
        
        with patch("httpx.AsyncClient.post", return_value=mock_response):
            client = DeepMindAIClient(api_key="test_key")
            result = await client.chat(
                messages=[{"role": "user", "content": "Hello"}],
                model="flagship",
            )
        
        assert result.content != ""
        assert result.model == "grok-4.20"
        assert result.total_tokens == 600
    
    @pytest.mark.asyncio
    async def test_chat_different_models(self):
        """Test chat with different models."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "response"}, "finish_reason": "stop"}],
            "usage": {},
        }
        
        with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
            client = DeepMindAIClient(api_key="test_key")
            
            # Test flagship model
            await client.chat([{"role": "user", "content": "test"}], model="flagship")
            call_args = mock_post.call_args[1]["json"]
            assert call_args["model"] == "grok-4.20"
            
            # Test mini model
            await client.chat([{"role": "user", "content": "test"}], model="mini")
            call_args = mock_post.call_args[1]["json"]
            assert call_args["model"] == "grok-3-mini"
    
    @pytest.mark.asyncio
    async def test_analyze_full_paper(self):
        """Test full paper analysis."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"research_question": "..."}'}, "finish_reason": "stop"}],
            "usage": {"total_tokens": 50000},
        }
        
        with patch("httpx.AsyncClient.post", return_value=mock_response):
            client = DeepMindAIClient(api_key="test_key")
            result = await client.analyze_full_paper(
                paper_text="This is a research paper...",
                analysis_type="comprehensive",
            )
        
        assert "analysis" in result
        assert result["tokens_used"] == 50000
        assert result["analysis_type"] == "comprehensive"
    
    @pytest.mark.asyncio
    async def test_analyze_full_paper_truncation(self):
        """Test paper truncation when exceeding context limit."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "analysis"}, "finish_reason": "stop"}],
            "usage": {},
        }
        
        with patch("httpx.AsyncClient.post", return_value=mock_response):
            client = DeepMindAIClient(api_key="test_key")
            
            # Very long paper (exceeds limit)
            long_paper = "x" * 2_000_000
            
            result = await client.analyze_full_paper(
                paper_text=long_paper,
                analysis_type="comprehensive",
            )
        
        # Should complete without error (truncation happens internally)
        assert "analysis" in result
    
    @pytest.mark.asyncio
    async def test_synthesize_papers(self):
        """Test multi-paper synthesis."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Synthesis of findings..."}, "finish_reason": "stop"}],
            "usage": {"total_tokens": 100000},
        }
        
        with patch("httpx.AsyncClient.post", return_value=mock_response):
            client = DeepMindAIClient(api_key="test_key")
            result = await client.synthesize_papers(
                papers=[
                    {"title": "Paper 1", "text": "Content 1"},
                    {"title": "Paper 2", "text": "Content 2"},
                ],
                synthesis_goal="hypothesis_generation",
            )
        
        assert "synthesis" in result
        assert result["papers_analyzed"] == 2
        assert result["synthesis_goal"] == "hypothesis_generation"
    
    def test_get_model_info(self):
        """Test getting model information."""
        client = DeepMindAIClient(api_key="test_key")
        info = client.get_model_info()
        
        assert info["provider"] == "DeepMind AI (xAI)"
        assert "models" in info
        assert "grok-4.20" in info["models"]
        assert "grok-4" in info["models"]
        assert "grok-3-mini" in info["models"]
        
        # Check 2M context feature
        assert info["models"]["grok-4.20"]["context_window"] == "2M tokens"


class TestFactoryFunctions:
    """Test factory functions."""
    
    def test_create_deepquery_client_with_key(self):
        """Test creating DeepQuery client with API key."""
        client = create_deepquery_client(api_key="test_key")
        
        assert isinstance(client, DeepQueryClient)
    
    def test_create_deepquery_client_from_env(self):
        """Test creating DeepQuery client from environment."""
        import os
        
        # Temporarily set env var
        old_value = os.environ.get("DEEPQUERY_API_KEY")
        os.environ["DEEPQUERY_API_KEY"] = "env_key"
        
        try:
            client = create_deepquery_client()
            assert isinstance(client, DeepQueryClient)
        finally:
            if old_value:
                os.environ["DEEPQUERY_API_KEY"] = old_value
            else:
                del os.environ["DEEPQUERY_API_KEY"]
    
    def test_create_deepquery_client_no_key_raises(self):
        """Test creating DeepQuery client without key raises error."""
        import os
        
        # Temporarily clear env var
        old_value = os.environ.get("DEEPQUERY_API_KEY")
        if "DEEPQUERY_API_KEY" in os.environ:
            del os.environ["DEEPQUERY_API_KEY"]
        
        try:
            with pytest.raises(ValueError, match="API key required"):
                create_deepquery_client()
        finally:
            if old_value:
                os.environ["DEEPQUERY_API_KEY"] = old_value
    
    def test_create_deepmind_ai_client_with_key(self):
        """Test creating DeepMind AI client with API key."""
        client = create_deepmind_ai_client(api_key="test_key")
        
        assert isinstance(client, DeepMindAIClient)
    
    def test_create_deepmind_ai_client_from_env(self):
        """Test creating DeepMind AI client from environment."""
        import os
        
        old_value = os.environ.get("DEEPMIND_AI_API_KEY")
        os.environ["DEEPMIND_AI_API_KEY"] = "env_key"
        
        try:
            client = create_deepmind_ai_client()
            assert isinstance(client, DeepMindAIClient)
        finally:
            if old_value:
                os.environ["DEEPMIND_AI_API_KEY"] = old_value
            else:
                del os.environ["DEEPMIND_AI_API_KEY"]
