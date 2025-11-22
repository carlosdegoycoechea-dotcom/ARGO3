"""
ARGO Hook Manager
Allows plugins to modify core behavior at specific points
"""

import logging
from typing import Callable, Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class HookPoint(Enum):
    """Predefined hook points in ARGO"""
    # Document processing hooks
    PRE_DOCUMENT_UPLOAD = "pre_document_upload"
    POST_DOCUMENT_UPLOAD = "post_document_upload"
    PRE_DOCUMENT_INDEX = "pre_document_index"
    POST_DOCUMENT_INDEX = "post_document_index"

    # RAG hooks
    PRE_RAG_SEARCH = "pre_rag_search"
    POST_RAG_SEARCH = "post_rag_search"
    PRE_RAG_RERANK = "pre_rag_rerank"
    POST_RAG_RERANK = "post_rag_rerank"

    # LLM hooks
    PRE_LLM_CALL = "pre_llm_call"
    POST_LLM_CALL = "post_llm_call"
    PRE_PROMPT_BUILD = "pre_prompt_build"
    POST_PROMPT_BUILD = "post_prompt_build"

    # Analysis hooks
    PRE_ANALYSIS = "pre_analysis"
    POST_ANALYSIS = "post_analysis"

    # Query processing hooks
    PRE_QUERY_PROCESSING = "pre_query_processing"
    POST_QUERY_PROCESSING = "post_query_processing"

    # Chunking hooks
    PRE_CHUNKING = "pre_chunking"
    POST_CHUNKING = "post_chunking"

    # Extraction hooks
    PRE_EXTRACTION = "pre_extraction"
    POST_EXTRACTION = "post_extraction"


class HookManager:
    """
    Hook system for extending core functionality

    Hooks allow plugins to intercept and modify data at specific points
    without modifying core code.

    Usage:
        # Register hook
        hooks.register(HookPoint.PRE_RAG_SEARCH, modify_query)

        # Execute hooks
        modified_query = hooks.execute(HookPoint.PRE_RAG_SEARCH, query)
    """

    def __init__(self):
        self.hooks: Dict[str, List[Callable]] = {}
        self.hook_stats: Dict[str, int] = {}

    def register(self, hook_point: str, callback: Callable, priority: int = 0):
        """
        Register a hook callback

        Args:
            hook_point: Hook point identifier (use HookPoint enum)
            callback: Function to call at this hook point
            priority: Higher priority hooks run first (default 0)
        """
        # Convert enum to string if needed
        if isinstance(hook_point, HookPoint):
            hook_point = hook_point.value

        if hook_point not in self.hooks:
            self.hooks[hook_point] = []
            self.hook_stats[hook_point] = 0

        # Store callback with priority
        self.hooks[hook_point].append((callback, priority))

        # Sort by priority (highest first)
        self.hooks[hook_point].sort(key=lambda x: x[1], reverse=True)

        logger.debug(f"🪝 Hook registered: {hook_point} -> {callback.__name__} (priority={priority})")

    def unregister(self, hook_point: str, callback: Callable):
        """
        Unregister a hook callback

        Args:
            hook_point: Hook point identifier
            callback: Callback to remove
        """
        if isinstance(hook_point, HookPoint):
            hook_point = hook_point.value

        if hook_point in self.hooks:
            self.hooks[hook_point] = [
                (cb, priority) for cb, priority in self.hooks[hook_point]
                if cb != callback
            ]
            logger.debug(f"🪝 Hook unregistered: {hook_point} -> {callback.__name__}")

    def execute(self, hook_point: str, data: Any, context: Optional[Dict] = None) -> Any:
        """
        Execute all hooks at a hook point

        Args:
            hook_point: Hook point identifier
            data: Data to pass through hooks
            context: Optional context dict for additional info

        Returns:
            Modified data after all hooks have processed it
        """
        if isinstance(hook_point, HookPoint):
            hook_point = hook_point.value

        hooks = self.hooks.get(hook_point, [])

        if not hooks:
            return data

        # Track execution
        self.hook_stats[hook_point] = self.hook_stats.get(hook_point, 0) + 1

        logger.debug(f"🪝 Executing {len(hooks)} hooks at: {hook_point}")

        result = data
        context = context or {}

        for callback, priority in hooks:
            try:
                # Call hook with data and context
                modified = callback(result, context)

                # Use modified data if hook returns something
                if modified is not None:
                    result = modified

            except Exception as e:
                logger.error(
                    f"❌ Hook error at {hook_point} -> {callback.__name__}: {e}"
                )
                # Continue with other hooks despite error

        return result

    async def execute_async(self, hook_point: str, data: Any, context: Optional[Dict] = None) -> Any:
        """
        Execute hooks asynchronously

        Args:
            hook_point: Hook point identifier
            data: Data to pass through hooks
            context: Optional context

        Returns:
            Modified data
        """
        import asyncio

        if isinstance(hook_point, HookPoint):
            hook_point = hook_point.value

        hooks = self.hooks.get(hook_point, [])

        if not hooks:
            return data

        self.hook_stats[hook_point] = self.hook_stats.get(hook_point, 0) + 1

        logger.debug(f"🪝 Executing {len(hooks)} hooks async at: {hook_point}")

        result = data
        context = context or {}

        for callback, priority in hooks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    modified = await callback(result, context)
                else:
                    modified = callback(result, context)

                if modified is not None:
                    result = modified

            except Exception as e:
                logger.error(
                    f"❌ Hook error at {hook_point} -> {callback.__name__}: {e}"
                )

        return result

    def has_hooks(self, hook_point: str) -> bool:
        """Check if there are any hooks registered at this point"""
        if isinstance(hook_point, HookPoint):
            hook_point = hook_point.value
        return bool(self.hooks.get(hook_point))

    def count_hooks(self, hook_point: str) -> int:
        """Count hooks at a specific point"""
        if isinstance(hook_point, HookPoint):
            hook_point = hook_point.value
        return len(self.hooks.get(hook_point, []))

    def list_hook_points(self) -> List[str]:
        """List all registered hook points"""
        return list(self.hooks.keys())

    def get_stats(self) -> Dict[str, int]:
        """Get hook execution statistics"""
        return self.hook_stats.copy()

    def clear_stats(self):
        """Clear execution statistics"""
        self.hook_stats.clear()
        logger.debug("Hook statistics cleared")

    def clear_hooks(self, hook_point: Optional[str] = None):
        """
        Clear hooks

        Args:
            hook_point: Specific hook point to clear, or None for all
        """
        if hook_point:
            if isinstance(hook_point, HookPoint):
                hook_point = hook_point.value
            if hook_point in self.hooks:
                self.hooks[hook_point].clear()
                logger.debug(f"🪝 Hooks cleared at: {hook_point}")
        else:
            self.hooks.clear()
            logger.debug("🪝 All hooks cleared")
