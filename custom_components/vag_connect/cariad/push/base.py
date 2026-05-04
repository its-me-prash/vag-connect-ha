# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Abstract base + value types for push managers.

All brand-specific push managers (Skoda MQTT, CUPRA/SEAT FCM, ...)
implement the same lifecycle so the coordinator can hold them
uniformly via ``self._push_manager: PushManager | None``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
import logging
from typing import Any, Awaitable, Callable

_LOGGER = logging.getLogger(__name__)


class PushManagerState(StrEnum):
    """Lifecycle phases of a push manager."""

    STOPPED = "stopped"
    STARTING = "starting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    DISABLED = "disabled"      # opt-out via option, no work attempted
    UNAVAILABLE = "unavailable"  # deps missing or broker unreachable


@dataclass(frozen=True)
class PushUpdateEvent:
    """A single push event from the manufacturer backend.

    Carries enough context for the coordinator to decide what to
    refresh — never the full state itself, since most VAG push events
    are change-notifications, not state-payloads.

    Attributes:
        vin: The 17-char VIN the event is for.
        event_type: Backend-defined string. For Skoda mysmob this is
            one of ``operation-request``, ``service-event``,
            ``account-event``, ``vehicle-event``. For CUPRA/SEAT FCM
            it's the FCM message type.
        topic: Full backend topic / channel string. Useful for
            debugging + coordinator-side filtering.
        timestamp: ISO-8601 UTC string of when the backend produced
            the event (NOT when we received it).
        raw_payload: Decoded JSON payload, if any. Some events carry
            full state slices; most are pure notifications.
    """

    vin: str
    event_type: str
    topic: str
    timestamp: str
    raw_payload: dict[str, Any] | None = None


# Coordinator callback signature — push manager fires this on each
# event so coordinator can refresh + async_set_updated_data.
PushEventCallback = Callable[[PushUpdateEvent], Awaitable[None]]


class PushManager(ABC):
    """Abstract base for brand-specific push managers.

    Subclasses MUST implement ``start()`` and ``stop()``. ``start``
    is fire-and-forget — it spawns its own background task so callers
    don't block. ``stop`` waits for clean shutdown.

    Subclasses SHOULD:
    - Lazy-import their network deps (aiomqtt, firebase-messaging)
      inside ``start()`` so non-opted-in users don't pay the install
      cost
    - Use exponential backoff on reconnect (5s → 600s with jitter)
    - Refresh OAuth tokens before each reconnect attempt
    - Log only masked VINs / user_ids — NEVER tokens
    """

    def __init__(self, on_event: PushEventCallback) -> None:
        self._on_event = on_event
        self._state: PushManagerState = PushManagerState.STOPPED

    @property
    def state(self) -> PushManagerState:
        """Current lifecycle state for diagnostics."""
        return self._state

    @abstractmethod
    async def start(self) -> None:
        """Spawn the background push connection.

        Idempotent — safe to call multiple times. If already connected
        or starting, returns immediately.
        """

    @abstractmethod
    async def stop(self) -> None:
        """Cleanly disconnect + cancel the background task.

        Idempotent. Waits for the task to finish (with timeout) so
        the caller can rely on resource release upon return.
        """

    async def emit(self, event: PushUpdateEvent) -> None:
        """Forward an event to the coordinator callback.

        Subclasses call this from their message-handler. Wrapped in
        try/except so a failing coordinator handler doesn't crash
        the push loop.
        """
        try:
            await self._on_event(event)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning(
                "Push event handler raised for vin ***%s (%s): %s — "
                "continuing push loop",
                event.vin[-6:] if event.vin else "??????",
                event.event_type,
                err,
            )
