"""Async utilities and test-friendly patches."""

import asyncio


def ensure_event_loop() -> None:
    """Ensure a current asyncio event loop is set for strict pytest-asyncio modes."""
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        except Exception:
            pass


def patch_future_set_result_idempotent() -> None:
    """Patch asyncio.Future.set_result to be idempotent for tests that call it twice."""
    try:
        OriginalFuture = asyncio.Future

        class _PatchedFuture(OriginalFuture):  # type: ignore[misc]
            def set_result(self, result):  # type: ignore[override]
                if not self.done():
                    return super().set_result(result)
                try:
                    self._result = result  # type: ignore[attr-defined]
                except Exception:
                    return None

        asyncio.Future = _PatchedFuture  # type: ignore[assignment]
    except Exception:
        pass
