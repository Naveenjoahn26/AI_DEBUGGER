"""
backend/app/services/debug_service.py

Business logic for the end-to-end debug pipeline:

    1. Validate URL
    2. Clone repo into temp dir  (RepositoryCloner)
    3. Index repo               (IndexingPipeline) — collection cleared first
    4. Run agent                (AgentRunner + SearchCodeTool)
       └─ retriever: HybridRetriever (BM25 + Semantic + RRF)   [FIX 1]
    5. Extract final diagnosis
    6. Return structured DebugResponse

Routers must not contain this logic; they call this service.
"""

import hashlib
import logging
import os
from pathlib import Path

from repository.agent.llm_adapter import GroqAgentLLM
from repository.agent.loop.runner import AgentRunner
from repository.agent.memory.store import MemoryStore
from repository.agent.state.models import IterationStatus, AgentState, ChatMessage, MessageRole
from repository.agent.tools.registry import ToolRegistry
from repository.agent.tools.search_code import SearchCodeTool
from repository.ai.context_builder import RepositoryContextBuilder
from repository.embeddings.embedder import CodeEmbedder
from repository.embeddings.vector_store import CodeVectorStore
from repository.exceptions import CloneFailedError, InvalidRepositoryURLError
from repository.ingestion.cloner import RepositoryCloner
from repository.ingestion.indexer import IndexingPipeline
from repository.retrieval.hybrid import HybridRetriever
from repository.retrieval.lexical import BM25Retriever
from repository.retrieval.semantic import SemanticRetriever

from app.schemas.debug import DebugMetadata, DebugRequest, DebugResponse, EvidenceItem, IterationInfo, ToolCallInfo
from app.services import event_bus

logger = logging.getLogger(__name__)


def _collection_name_for(repo_url: str) -> str:
    """Derive a short, unique ChromaDB collection name from the repo URL."""
    digest = hashlib.sha256(repo_url.encode()).hexdigest()[:12]
    return f"ai_debugger_{digest}"


def _extract_final_diagnosis(state) -> str:
    """
    Walk the agent state messages in reverse and return the last
    assistant message content. Falls back to an empty string.
    """
    for message in reversed(state.messages):
        role = message.role.value if hasattr(message.role, "value") else message.role
        if role == "assistant" and message.content:
            return message.content
    return ""


class DebugService:
    """
    Orchestrates the full debug pipeline.

    Each call:
     - clones the repo into a temporary directory
     - clears stale ChromaDB data for the collection  [FIX A]
     - indexes the repo using HybridRetriever          [FIX 1]
     - runs the agent
     - cleans up on exit
    """

    def __init__(
        self,
        chroma_dir: str | None = None,
        max_agent_iterations: int = 5,
    ) -> None:
        self._chroma_dir = chroma_dir or os.getenv("CHROMA_DIR", "./chroma_db")
        self._max_iterations = max_agent_iterations

    def run(self, request: DebugRequest, session_id: str | None = None) -> DebugResponse:
        """
        Execute the full debug pipeline for *request*.
        """
        repo_url = request.repo_url
        collection_name = _collection_name_for(repo_url)

        logger.info(
            "debug_service_start",
            extra={"repo_url": repo_url, "collection": collection_name},
        )

        self._emit(session_id, "debug_request_received", "Debug request received", {
            "repo_url": repo_url,
        })

        self._emit(session_id, "cloning_repository", "Cloning repository...")

        with RepositoryCloner.clone(repo_url) as repo_path:
            self._emit(session_id, "clone_complete", "Repository cloned successfully")

            summary, state = self._run_pipeline(
                repo_path=repo_path,
                bug_description=request.bug_description,
                collection_name=collection_name,
                session_id=session_id,
            )

        diagnosis = _extract_final_diagnosis(state)
        
        # Prepend syntax error warning if present
        if getattr(summary, "errors", None) and diagnosis:
            syntax_errs = [err for err in summary.errors if "SyntaxError" in err or "chunk_error" in err]
            if syntax_errs:
                warning = f"**Warning:** Several files contain syntax errors and could not be analyzed. This might be related to the bug. Check files like: {syntax_errs[0].split(':')[1].strip()}\n\n"
                diagnosis = warning + diagnosis

        files_list, iterations_list, evidence_list = self._build_response_data(summary, state)

        if not diagnosis:
            if evidence_list:
                ev_files = list({ev.file_path for ev in evidence_list})
                diagnosis = (
                    "### 🔍 Investigation Summary\n\n"
                    f"The agent investigated the repository and identified relevant code in: "
                    + ", ".join(f"`{f}`" for f in ev_files[:5]) + ".\n\n"
                    "**Observed Findings:**\n"
                    "Review the retrieved functions and line ranges in the **Evidence** panel below "
                    "for direct inspection of the affected logic."
                )
            else:
                diagnosis = (
                    "### 🔍 Investigation Completed\n\n"
                    "The repository was indexed and searched, but the query did not yield high-confidence matches. "
                    "Please check the **Files** panel on the left to see all scanned files, or refine the bug description with specific function names or error keywords."
                )

        logger.info(
            "debug_service_success",
            extra={"iterations": state.iteration},
        )

        self._emit(session_id, "debug_service_success", "Diagnosis complete", {
            "iterations": state.iteration,
            "status": "success",
        })

        return DebugResponse(
            status="success",
            diagnosis=diagnosis,
            repository=repo_url,
            metadata=DebugMetadata(
                input_tokens=state.input_tokens,
                output_tokens=state.output_tokens,
                total_tokens=state.total_tokens,
                estimated_cost=state.estimated_cost,
                iterations=state.iteration,
                files_indexed=summary.files_processed,
                chunks_indexed=summary.chunks_indexed,
            ),
            files=files_list,
            iterations=iterations_list,
            evidence=evidence_list,
        )

        return DebugResponse(
            status="success",
            diagnosis=diagnosis,
            repository=repo_url,
            metadata=DebugMetadata(
                input_tokens=state.input_tokens,
                output_tokens=state.output_tokens,
                total_tokens=state.total_tokens,
                estimated_cost=state.estimated_cost,
                iterations=state.iteration,
                files_indexed=summary.files_processed,
                chunks_indexed=summary.chunks_indexed,
            ),
            files=files_list,
            iterations=iterations_list,
            evidence=evidence_list,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_response_data(self, summary, state):
        import re

        files_list = list({chunk.file_path for chunk in getattr(summary, "_chunks", [])})
        
        iterations_list = []
        current_iter = 1
        for msg in state.messages:
            role = msg.role.value if hasattr(msg.role, "value") else msg.role
            if role == "assistant" and getattr(msg, "tool_calls", None):
                tcs = [ToolCallInfo(name=tc.name, tool_call_id=tc.id, arguments=tc.arguments) for tc in msg.tool_calls]
                iterations_list.append(IterationInfo(iteration=current_iter, tool_calls=tcs))
                current_iter += 1

        evidence_list = []
        seen_evidence = set()
        for obs in getattr(state, "observations", []):
            content = getattr(obs, "content", "")
            # Look for blocks formatted by ContextBuilder
            # File: ..., Type: ..., Name: ..., Lines: X-Y\n```python\n...\n```
            pattern = re.compile(r"File:\s*([^\n]+)\nType:\s*([^\n]+)\nName:\s*([^\n]+)\nLines:\s*(\d+)-(\d+)\n```python\n(.*?)\n```", re.DOTALL)
            for match in pattern.finditer(content):
                file_path = match.group(1).strip()
                name = match.group(3).strip()
                start_line = int(match.group(4))
                end_line = int(match.group(5))
                code = match.group(6).strip()
                
                key = f"{file_path}:{start_line}:{end_line}"
                if key not in seen_evidence:
                    seen_evidence.add(key)
                    evidence_list.append(EvidenceItem(
                        file_path=file_path,
                        function_name=name if name != 'anonymous' else None,
                        start_line=start_line,
                        end_line=end_line,
                        code=code
                    ))

        return files_list, iterations_list, evidence_list

    def _emit(self, session_id: str | None, event: str, message: str, data: dict | None = None):
        if session_id:
            event_bus.emit(session_id, event, message, data)

    def _run_pipeline(
        self,
        repo_path: Path,
        bug_description: str,
        collection_name: str,
        session_id: str | None = None,
    ):
        """Build all components, index the repo, and run the agent."""

        # 1. Set up embedder + vector store
        embedder = CodeEmbedder()
        vector_store = CodeVectorStore(
            collection_name=collection_name,
            persist_directory=self._chroma_dir,
        )

        # FIX A: clear stale chunks from previous runs on the same URL
        vector_store.clear()
        logger.info("vector_store_cleared", extra={"collection": collection_name})

        # 2. Index the repository
        self._emit(session_id, "indexing_start", "Indexing repository...")
        pipeline = IndexingPipeline(embedder=embedder, vector_store=vector_store)
        summary = pipeline.run(repo_path)
        self._emit(session_id, "indexing_complete",
                   f"Indexed {summary.files_processed} files, {summary.chunks_indexed} chunks",
                   {
                       "files_scanned": summary.files_scanned,
                       "files_processed": summary.files_processed,
                       "chunks_created": summary.chunks_created,
                       "chunks_indexed": summary.chunks_indexed,
                   })


        # 3. FIX 1: build HybridRetriever (BM25 + Semantic + RRF)
        #    instead of pure-semantic CodeRetriever
        context_builder = RepositoryContextBuilder()

        # We need the full chunk list for BM25 — re-read from vector store
        # by doing a broad semantic search with a dummy embedding of zeros,
        # OR re-use the chunks from the indexing summary. The cleanest approach
        # is to keep a reference from the pipeline run.
        semantic_retriever = SemanticRetriever(
            embedder=embedder,
            vector_store=vector_store,
        )

        # Build BM25 from the chunks discovered during indexing
        # The IndexingPipeline doesn't expose its chunk list directly,
        # so we rebuild BM25 from what was indexed (stored in vector store).
        # We pass an empty list if indexing produced no chunks — BM25Retriever
        # handles that gracefully.
        all_chunks = getattr(summary, "_chunks", [])
        lexical_retriever = BM25Retriever(chunks=all_chunks)

        retriever = HybridRetriever(
            semantic_retriever=semantic_retriever,
            lexical_retriever=lexical_retriever,
        )

        search_tool = SearchCodeTool(
            retriever=retriever,
            context_builder=context_builder,
        )

        # 4. Build tool registry
        registry = ToolRegistry()
        registry.register(search_tool)

        # 5. Build LLM adapter
        llm = GroqAgentLLM(tools=registry.get_all_tools())

        # FIX E: inject MemoryStore so the agent's memory feature is active
        memory_store = MemoryStore()

        # 6. Run agent
        self._emit(session_id, "agent_started", "Agent started reasoning...")
        agent = AgentRunner(
            llm=llm,
            tool_registry=registry,
            memory_store=memory_store,
            max_iterations=self._max_iterations,
        )
        state = agent.run(goal=bug_description)

        # Emit tool call events
        for tc in state.tool_calls:
            self._emit(session_id, "tool_called", f"Tool: {tc.name}", {
                "tool_name": tc.name,
                "tool_call_id": tc.id,
                "arguments": tc.arguments,
            })

        # Emit token usage
        self._emit(session_id, "token_usage", "Token usage calculated", {
            "input_tokens": state.input_tokens,
            "output_tokens": state.output_tokens,
            "total_tokens": state.total_tokens,
            "estimated_cost": state.estimated_cost,
            "iterations": state.iteration,
        })

        return summary, state
