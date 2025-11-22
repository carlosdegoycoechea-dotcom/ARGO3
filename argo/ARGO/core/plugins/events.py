"""
ARGO Event Bus
Event-driven communication system for plugins
"""

import logging
import asyncio
from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event handler priority"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    """Event data structure"""
    name: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL


class EventBus:
    """
    Event bus for plugin communication

    Usage:
        # Register handler
        events.on('document_uploaded', handler_function)

        # Emit event
        events.emit('document_uploaded', {'file': 'test.pdf'})

        # Async emit
        await events.emit_async('document_uploaded', {'file': 'test.pdf'})
    """

    def __init__(self):
        self.handlers: Dict[str, List[tuple[Callable, EventPriority]]] = {}
        self.event_history: List[Event] = []
        self.max_history = 100

    def on(self, event_name: str, handler: Callable, priority: EventPriority = EventPriority.NORMAL):
        """
        Register an event handler

        Args:
            event_name: Name of event to listen for
            handler: Function to call when event occurs
            priority: Handler priority (higher priority runs first)
        """
        if event_name not in self.handlers:
            self.handlers[event_name] = []

        self.handlers[event_name].append((handler, priority))

        # Sort by priority (highest first)
        self.handlers[event_name].sort(key=lambda x: x[1].value, reverse=True)

        logger.debug(f"📌 Event handler registered: {event_name} -> {handler.__name__}")

    def off(self, event_name: str, handler: Callable):
        """
        Unregister an event handler

        Args:
            event_name: Event name
            handler: Handler to remove
        """
        if event_name in self.handlers:
            self.handlers[event_name] = [
                (h, p) for h, p in self.handlers[event_name] if h != handler
            ]
            logger.debug(f"📌 Event handler removed: {event_name} -> {handler.__name__}")

    def emit_sync(self, event_name: str, data: Dict[str, Any], source: Optional[str] = None):
        """
        Emit event synchronously

        Args:
            event_name: Name of event
            data: Event data
            source: Source of event (e.g., plugin name)
        """
        event = Event(name=event_name, data=data, source=source)
        self._add_to_history(event)

        handlers = self.handlers.get(event_name, [])

        if not handlers:
            logger.debug(f"📢 Event emitted (no handlers): {event_name}")
            return

        logger.debug(f"📢 Event emitted: {event_name} -> {len(handlers)} handlers")

        for handler, priority in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(
                    f"❌ Event handler error: {event_name} -> {handler.__name__}: {e}"
                )

    async def emit_async(self, event_name: str, data: Dict[str, Any], source: Optional[str] = None):
        """
        Emit event asynchronously

        Args:
            event_name: Name of event
            data: Event data
            source: Source of event
        """
        event = Event(name=event_name, data=data, source=source)
        self._add_to_history(event)

        handlers = self.handlers.get(event_name, [])

        if not handlers:
            logger.debug(f"📢 Event emitted async (no handlers): {event_name}")
            return

        logger.debug(f"📢 Event emitted async: {event_name} -> {len(handlers)} handlers")

        tasks = []
        for handler, priority in handlers:
            task = self._run_handler_async(handler, data, event_name)
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_handler_async(self, handler: Callable, data: Dict[str, Any], event_name: str):
        """Run handler safely with error handling"""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(data)
            else:
                # Run sync handler in executor to not block
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, handler, data)
        except Exception as e:
            logger.error(
                f"❌ Event handler error: {event_name} -> {handler.__name__}: {e}"
            )

    def emit(self, event_name: str, data: Dict[str, Any], source: Optional[str] = None):
        """
        Emit event (detects async context automatically)

        Args:
            event_name: Name of event
            data: Event data
            source: Source of event
        """
        try:
            # Try to get running event loop
            loop = asyncio.get_running_loop()
            # We're in async context, create task
            asyncio.create_task(self.emit_async(event_name, data, source))
        except RuntimeError:
            # No event loop, use sync
            self.emit_sync(event_name, data, source)

    def _add_to_history(self, event: Event):
        """Add event to history"""
        self.event_history.append(event)

        # Trim history if too long
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]

    def get_history(self, event_name: Optional[str] = None, limit: int = 10) -> List[Event]:
        """
        Get event history

        Args:
            event_name: Filter by event name (None for all)
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        if event_name:
            filtered = [e for e in self.event_history if e.name == event_name]
        else:
            filtered = self.event_history

        return filtered[-limit:]

    def clear_history(self):
        """Clear event history"""
        self.event_history.clear()
        logger.debug("Event history cleared")

    def list_events(self) -> List[str]:
        """List all registered event names"""
        return list(self.handlers.keys())

    def count_handlers(self, event_name: str) -> int:
        """Count handlers for an event"""
        return len(self.handlers.get(event_name, []))
