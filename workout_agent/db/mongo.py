"""MongoDB connection utilities."""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase


class MongoConnection:
    """Simple MongoDB connection manager for async repositories."""

    def __init__(self, uri: str, db_name: str) -> None:
        self._client = AsyncIOMotorClient(uri)
        self._db = self._client[db_name]

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Return active database."""

        return self._db

    def collection(self, name: str) -> AsyncIOMotorCollection:
        """Return collection by name."""

        return self._db[name]

    async def ping(self) -> bool:
        """Ping database to verify connectivity."""

        await self._db.command("ping")
        return True

    def close(self) -> None:
        """Close the underlying Mongo client."""

        self._client.close()
