import asyncio
import time

from services.live_game import ingest_live_game_for_frontend


DEFAULT_CACHE_TTL_SECONDS = 5

_LIVE_GAME_CACHE = {}
_CACHE_LOCKS = {}


def _cache_key(game_id, season, pitcher_id):
    return (int(game_id), int(season), int(pitcher_id) if pitcher_id is not None else None)


def _get_lock(cache_key):
    lock = _CACHE_LOCKS.get(cache_key)
    if lock is None:
        lock = asyncio.Lock()
        _CACHE_LOCKS[cache_key] = lock
    return lock


def _is_fresh(cache_entry, ttl_seconds):
    return cache_entry and time.monotonic() - cache_entry["fetched_at"] < ttl_seconds


async def get_cached_live_game(
    game_id,
    season,
    pitcher_id=None,
    ttl_seconds=DEFAULT_CACHE_TTL_SECONDS,
    force_refresh=False,
):
    cache_key = _cache_key(game_id, season, pitcher_id)
    cached = _LIVE_GAME_CACHE.get(cache_key)

    if not force_refresh and _is_fresh(cached, ttl_seconds):
        return cached["data"]

    async with _get_lock(cache_key):
        cached = _LIVE_GAME_CACHE.get(cache_key)

        if not force_refresh and _is_fresh(cached, ttl_seconds):
            return cached["data"]

        data = await ingest_live_game_for_frontend(
            game_id,
            season,
            pitcher_id=pitcher_id,
        )

        _LIVE_GAME_CACHE[cache_key] = {
            "fetched_at": time.monotonic(),
            "data": data,
        }

        return data


def clear_live_game_cache(game_id=None, season=None, pitcher_id=None):
    if game_id is None and season is None and pitcher_id is None:
        _LIVE_GAME_CACHE.clear()
        return

    cache_key = _cache_key(game_id, season, pitcher_id)
    _LIVE_GAME_CACHE.pop(cache_key, None)


def get_live_game_cache_snapshot():
    now = time.monotonic()

    return {
        cache_key: {
            "age_seconds": round(now - cache_entry["fetched_at"], 2),
            "game_id": cache_entry["data"].get("game_id"),
            "season": cache_entry["data"].get("season"),
            "pitcher_count": len(cache_entry["data"].get("pitchers", [])),
        }
        for cache_key, cache_entry in _LIVE_GAME_CACHE.items()
    }
