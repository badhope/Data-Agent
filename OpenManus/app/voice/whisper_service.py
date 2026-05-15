"""Whisper语音识别服务 - 使用OpenAI Whisper实现高质量语音识别"""
import os
import io
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    import whisper
    from whisper import load_model
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

@dataclass
class TranscriptionResult:
    """语音识别结果"""
    text: str
    language: str
    confidence: float
    segments: Optional[list] = None
    error: Optional[str] = None

class WhisperService:
    """Whisper语音识别服务"""
    
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self.model = None
        self._lock = asyncio.Lock()
        
        if WHISPER_AVAILABLE:
            self._load_model_async()
    
    async def _load_model_async(self):
        """异步加载模型"""
        loop = asyncio.get_event_loop()
        self.model = await loop.run_in_executor(None, self._load_model_sync)
    
    def _load_model_sync(self):
        """同步加载模型"""
        try:
            return load_model(self.model_name)
        except Exception as e:
            print(f"加载Whisper模型失败: {e}")
            return None
    
    async def transcribe(self, audio_data: bytes, language: Optional[str] = None) -> TranscriptionResult:
        """
        转录音频数据
        
        Args:
            audio_data: 音频数据（bytes）
            language: 指定语言（可选）
        
        Returns:
            TranscriptionResult: 识别结果
        """
        if not WHISPER_AVAILABLE:
            return TranscriptionResult(
                text="",
                language="",
                confidence=0.0,
                error="Whisper未安装，请安装: pip install openai-whisper"
            )
        
        if self.model is None:
            return TranscriptionResult(
                text="",
                language="",
                confidence=0.0,
                error="模型未加载"
            )
        
        async with self._lock:
            try:
                # 将音频数据写入临时文件或BytesIO
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self._transcribe_sync, audio_data, language)
                return result
            except Exception as e:
                return TranscriptionResult(
                    text="",
                    language="",
                    confidence=0.0,
                    error=str(e)
                )
    
    def _transcribe_sync(self, audio_data: bytes, language: Optional[str]) -> TranscriptionResult:
        """同步转录"""
        # 使用BytesIO处理音频数据
        audio_file = io.BytesIO(audio_data)
        
        # 保存为临时文件（Whisper需要文件路径）
        temp_path = "/tmp/transcribe_audio.wav"
        with open(temp_path, 'wb') as f:
            f.write(audio_data)
        
        try:
            # 调用Whisper进行转录
            result = self.model.transcribe(
                temp_path,
                language=language,
                verbose=False
            )
            
            # 清理临时文件
            os.remove(temp_path)
            
            return TranscriptionResult(
                text=result.get("text", ""),
                language=result.get("language", ""),
                confidence=1.0,
                segments=result.get("segments", None)
            )
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
    
    async def transcribe_file(self, file_path: str, language: Optional[str] = None) -> TranscriptionResult:
        """
        转录音频文件
        
        Args:
            file_path: 音频文件路径
            language: 指定语言（可选）
        
        Returns:
            TranscriptionResult: 识别结果
        """
        if not WHISPER_AVAILABLE:
            return TranscriptionResult(
                text="",
                language="",
                confidence=0.0,
                error="Whisper未安装"
            )
        
        if self.model is None:
            return TranscriptionResult(
                text="",
                language="",
                confidence=0.0,
                error="模型未加载"
            )
        
        async with self._lock:
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self._transcribe_file_sync, file_path, language)
                return result
            except Exception as e:
                return TranscriptionResult(
                    text="",
                    language="",
                    confidence=0.0,
                    error=str(e)
                )
    
    def _transcribe_file_sync(self, file_path: str, language: Optional[str]) -> TranscriptionResult:
        """同步转录文件"""
        result = self.model.transcribe(
            file_path,
            language=language,
            verbose=False
        )
        
        return TranscriptionResult(
            text=result.get("text", ""),
            language=result.get("language", ""),
            confidence=1.0,
            segments=result.get("segments", None)
        )
    
    def get_supported_languages(self) -> list:
        """获取支持的语言列表"""
        if not WHISPER_AVAILABLE:
            return []
        
        return whisper.tokenizer.LANGUAGES
    
    def detect_language(self, audio_data: bytes) -> str:
        """检测音频语言"""
        if not WHISPER_AVAILABLE or self.model is None:
            return "unknown"
        
        try:
            temp_path = "/tmp/detect_audio.wav"
            with open(temp_path, 'wb') as f:
                f.write(audio_data)
            
            audio = whisper.load_audio(temp_path)
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
            
            _, probs = self.model.detect_language(mel)
            detected_lang = max(probs, key=probs.get)
            
            os.remove(temp_path)
            return detected_lang
        except Exception:
            return "unknown"
    
    @staticmethod
    def is_available() -> bool:
        """检查Whisper是否可用"""
        return WHISPER_AVAILABLE
    
    @staticmethod
    def get_model_sizes() -> dict:
        """获取可用的模型大小"""
        return {
            "tiny": "约1GB，速度快，准确率较低",
            "base": "约1.5GB，平衡速度和准确率",
            "small": "约2.4GB，较好的准确率",
            "medium": "约5.2GB，高准确率",
            "large": "约15GB，最高准确率"
        }

# 全局实例
whisper_service = None

def get_whisper_service(model_name: str = "base") -> WhisperService:
    """获取全局Whisper服务实例"""
    global whisper_service
    if whisper_service is None:
        whisper_service = WhisperService(model_name)
    return whisper_service