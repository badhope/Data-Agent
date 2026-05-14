from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import BaseChatMessageHistory
import redis
import json
import hashlib
from ..utils.logger import get_logger

logger = get_logger(__name__)

class RedisChatHistory(BaseChatMessageHistory):
    def __init__(self, session_id: str, redis_url: str = "redis://localhost:6379"):
        self.session_id = session_id
        self.redis_client = redis.from_url(redis_url)
        self.key = f"chat_history:{session_id}"
        self.ttl = 86400 * 7
    
    @property
    def messages(self) -> List[BaseMessage]:
        try:
            data = self.redis_client.get(self.key)
            if data:
                items = json.loads(data)
                return [self._deserialize_message(item) for item in items]
            return []
        except Exception as e:
            logger.error(f"Failed to load messages: {e}")
            return []
    
    def add_message(self, message: BaseMessage) -> None:
        try:
            messages = self.messages
            messages.append(message)
            serialized = [self._serialize_message(msg) for msg in messages]
            self.redis_client.set(self.key, json.dumps(serialized), ex=self.ttl)
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
    
    def clear(self) -> None:
        try:
            self.redis_client.delete(self.key)
        except Exception as e:
            logger.error(f"Failed to clear messages: {e}")
    
    def _serialize_message(self, message: BaseMessage) -> Dict:
        return {
            "type": message.type,
            "content": message.content,
            "additional_kwargs": message.additional_kwargs,
            "timestamp": datetime.now().isoformat()
        }
    
    def _deserialize_message(self, item: Dict) -> BaseMessage:
        msg_type = item.get("type", "human")
        content = item.get("content", "")
        
        if msg_type == "human":
            return HumanMessage(content=content)
        elif msg_type == "ai":
            return AIMessage(content=content)
        elif msg_type == "system":
            return SystemMessage(content=content)
        return HumanMessage(content=content)

class MemoryManager:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
    
    def get_chat_history(self, session_id: str) -> RedisChatHistory:
        return RedisChatHistory(session_id, self.redis_url)
    
    def generate_session_id(self) -> str:
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()
    
    def get_session_summary(self, session_id: str) -> Optional[str]:
        try:
            history = self.get_chat_history(session_id)
            messages = history.messages
            
            if len(messages) < 2:
                return None
            
            summary_key = f"session_summary:{session_id}"
            summary = self._get_redis_client().get(summary_key)
            return summary.decode() if summary else None
        except Exception as e:
            logger.error(f"Failed to get session summary: {e}")
            return None
    
    def update_session_summary(self, session_id: str, summary: str) -> None:
        try:
            client = self._get_redis_client()
            summary_key = f"session_summary:{session_id}"
            client.set(summary_key, summary, ex=self.ttl)
        except Exception as e:
            logger.error(f"Failed to update session summary: {e}")
    
    def delete_session(self, session_id: str) -> None:
        try:
            client = self._get_redis_client()
            client.delete(f"chat_history:{session_id}")
            client.delete(f"session_summary:{session_id}")
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
    
    def _get_redis_client(self) -> redis.Redis:
        return redis.from_url(self.redis_url)