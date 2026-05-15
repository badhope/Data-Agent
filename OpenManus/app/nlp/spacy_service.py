"""spaCy NLP服务 - 使用spaCy实现高级文本处理"""
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

@dataclass
class Entity:
    """命名实体"""
    text: str
    label: str
    start: int
    end: int
    confidence: float = 1.0

@dataclass
class Token:
    """词元信息"""
    text: str
    lemma: str
    pos: str
    tag: str
    dep: str
    shape: str
    is_stop: bool

@dataclass
class Sentence:
    """句子信息"""
    text: str
    start: int
    end: int
    tokens: List[Token] = None

@dataclass
class NLPResult:
    """NLP处理结果"""
    success: bool
    text: str = ""
    tokens: List[Token] = None
    entities: List[Entity] = None
    sentences: List[Sentence] = None
    noun_chunks: List[str] = None
    error: str = ""

class SpacyService:
    """spaCy NLP服务"""
    
    def __init__(self, model_name: str = "zh_core_web_sm"):
        self.model_name = model_name
        self.nlp = None
        self._lock = asyncio.Lock()
        
        if SPACY_AVAILABLE:
            self._load_model_async()
    
    async def _load_model_async(self):
        """异步加载模型"""
        loop = asyncio.get_event_loop()
        self.nlp = await loop.run_in_executor(None, self._load_model_sync)
    
    def _load_model_sync(self):
        """同步加载模型"""
        try:
            return spacy.load(self.model_name)
        except Exception as e:
            print(f"加载spaCy模型失败: {e}")
            print("尝试下载模型...")
            try:
                from spacy.cli import download
                download(self.model_name)
                return spacy.load(self.model_name)
            except Exception as de:
                print(f"下载模型失败: {de}")
                return None
    
    async def process(self, text: str) -> NLPResult:
        """
        处理文本，提取各种NLP信息
        
        Args:
            text: 输入文本
        
        Returns:
            NLPResult: 处理结果
        """
        if not SPACY_AVAILABLE:
            return NLPResult(
                success=False,
                error="spaCy未安装，请安装: pip install spacy"
            )
        
        if self.nlp is None:
            return NLPResult(
                success=False,
                error="模型未加载"
            )
        
        async with self._lock:
            try:
                doc = self.nlp(text)
                
                tokens = []
                for token in doc:
                    tokens.append(Token(
                        text=token.text,
                        lemma=token.lemma_,
                        pos=token.pos_,
                        tag=token.tag_,
                        dep=token.dep_,
                        shape=token.shape_,
                        is_stop=token.is_stop
                    ))
                
                entities = []
                for ent in doc.ents:
                    entities.append(Entity(
                        text=ent.text,
                        label=ent.label_,
                        start=ent.start_char,
                        end=ent.end_char
                    ))
                
                sentences = []
                for sent in doc.sents:
                    sent_tokens = []
                    for token in sent:
                        sent_tokens.append(Token(
                            text=token.text,
                            lemma=token.lemma_,
                            pos=token.pos_,
                            tag=token.tag_,
                            dep=token.dep_,
                            shape=token.shape_,
                            is_stop=token.is_stop
                        ))
                    sentences.append(Sentence(
                        text=sent.text,
                        start=sent.start_char,
                        end=sent.end_char,
                        tokens=sent_tokens
                    ))
                
                noun_chunks = [chunk.text for chunk in doc.noun_chunks]
                
                return NLPResult(
                    success=True,
                    text=text,
                    tokens=tokens,
                    entities=entities,
                    sentences=sentences,
                    noun_chunks=noun_chunks
                )
            
            except Exception as e:
                return NLPResult(
                    success=False,
                    error=f"NLP处理失败: {str(e)}"
                )
    
    async def extract_entities(self, text: str) -> List[Entity]:
        """
        提取命名实体
        
        Args:
            text: 输入文本
        
        Returns:
            List[Entity]: 实体列表
        """
        result = await self.process(text)
        return result.entities if result.success else []
    
    async def get_sentences(self, text: str) -> List[str]:
        """
        分句
        
        Args:
            text: 输入文本
        
        Returns:
            List[str]: 句子列表
        """
        result = await self.process(text)
        if result.success and result.sentences:
            return [sent.text for sent in result.sentences]
        return []
    
    async def lemmatize(self, text: str) -> str:
        """
        词性还原
        
        Args:
            text: 输入文本
        
        Returns:
            str: 还原后的文本
        """
        if not SPACY_AVAILABLE or self.nlp is None:
            return text
        
        async with self._lock:
            doc = self.nlp(text)
            return " ".join([token.lemma_ for token in doc])
    
    async def extract_noun_chunks(self, text: str) -> List[str]:
        """
        提取名词短语
        
        Args:
            text: 输入文本
        
        Returns:
            List[str]: 名词短语列表
        """
        result = await self.process(text)
        return result.noun_chunks if result.success else []
    
    async def pos_tagging(self, text: str) -> List[Dict[str, str]]:
        """
        词性标注
        
        Args:
            text: 输入文本
        
        Returns:
            List[Dict]: 词性标注结果
        """
        result = await self.process(text)
        if result.success and result.tokens:
            return [{
                'text': token.text,
                'pos': token.pos,
                'tag': token.tag
            } for token in result.tokens]
        return []
    
    def get_entity_labels(self) -> Dict[str, str]:
        """获取实体标签说明"""
        if not SPACY_AVAILABLE or self.nlp is None:
            return {}
        
        return self.nlp.get_pipe("ner").labels
    
    @staticmethod
    def is_available() -> bool:
        """检查spaCy是否可用"""
        return SPACY_AVAILABLE
    
    @staticmethod
    def get_available_models() -> List[str]:
        """获取可用的模型列表"""
        return [
            "zh_core_web_sm",
            "zh_core_web_md",
            "zh_core_web_lg",
            "en_core_web_sm",
            "en_core_web_md",
            "en_core_web_lg",
            "ja_core_news_sm",
            "ko_core_news_sm"
        ]

# 全局实例
nlp_service = None

def get_nlp_service(model_name: str = "zh_core_web_sm") -> SpacyService:
    """获取全局NLP服务实例"""
    global nlp_service
    if nlp_service is None:
        nlp_service = SpacyService(model_name)
    return nlp_service