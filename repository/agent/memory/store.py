from typing import List, Optional
from repository.agent.memory.models import Memory

class MemoryStore:
    def __init__(self):
        self._memory = {}

    def save(self, memory: Memory) -> None:
        """Saves or updates a Memory object in the store."""
        self._memory[memory.key] = memory

    def get(self, key: str) -> Optional[Memory]:
        """Retrieves a Memory object by its key."""
        return self._memory.get(key)

    def delete(self, key: str) -> None:
        """Deletes a Memory object by its key."""
        if key in self._memory:
            del self._memory[key]

    def reset(self) -> None:
        """Clears all memories from the store."""
        self._memory.clear()

    def search(self, query: str, limit: int = 5) -> List[Memory]:
        """Finds memories whose content or key is relevant to the query using simple keyword matching."""
        if not query or not query.strip():
            return []

        query_terms = query.lower().split()
        scored_memories = []

        for mem in self._memory.values():
            score = 0
            text_to_search = (mem.key + " " + mem.content).lower()
            
            # Simple scoring: +1 for every matching term
            for term in query_terms:
                if term in text_to_search:
                    score += 1
            
            # If there's any relevance, consider it
            if score > 0:
                scored_memories.append((score, mem))

        # Sort by score descending
        scored_memories.sort(key=lambda x: x[0], reverse=True)

        # Return the top N
        return [mem for score, mem in scored_memories[:limit]]