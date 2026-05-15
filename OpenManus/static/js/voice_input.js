/**
 * 语音输入工具 - Voice Input Module
 * 使用 Web Speech API 实现语音识别功能
 * 支持中文、英文等多种语言
 */

class VoiceInput {
    constructor(options = {}) {
        this.recognition = null;
        this.isListening = false;
        this.language = options.language || 'zh-CN';
        this.onResult = options.onResult || ((text) => console.log('识别结果:', text));
        this.onError = options.onError || ((error) => console.error('语音识别错误:', error));
        this.onStart = options.onStart || (() => {});
        this.onEnd = options.onEnd || (() => {});

        this.init();
    }

    init() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.warn('当前浏览器不支持 Web Speech API');
            this.isSupported = false;
            return;
        }

        this.isSupported = true;
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();

        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = this.language;
        this.recognition.maxAlternatives = 1;

        this.recognition.onstart = () => {
            this.isListening = true;
            this.onStart();
        };

        this.recognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }

            if (finalTranscript) {
                this.onResult(finalTranscript);
            }

            if (interimTranscript) {
                this.onResult(interimTranscript, true);
            }
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.isListening = false;

            let errorMessage = '语音识别出错';
            switch (event.error) {
                case 'no-speech':
                    errorMessage = '没有检测到语音，请重试';
                    break;
                case 'audio-capture':
                    errorMessage = '无法访问麦克风，请检查权限设置';
                    break;
                case 'not-allowed':
                    errorMessage = '麦克风访问被拒绝，请在浏览器设置中允许访问';
                    break;
                case 'network':
                    errorMessage = '网络错误，语音识别服务不可用';
                    break;
                case 'aborted':
                    errorMessage = '语音识别已停止';
                    break;
                case 'service-not-allowed':
                    errorMessage = '语音识别服务未授权';
                    break;
            }

            this.onError({
                error: event.error,
                message: errorMessage
            });
        };

        this.recognition.onend = () => {
            this.isListening = false;
            this.onEnd();
        };
    }

    start() {
        if (!this.isSupported) {
            this.onError({
                error: 'not-supported',
                message: '当前浏览器不支持语音识别功能'
            });
            return false;
        }

        if (this.isListening) {
            return false;
        }

        try {
            this.recognition.start();
            return true;
        } catch (e) {
            console.error('启动语音识别失败:', e);
            return false;
        }
    }

    stop() {
        if (this.isListening && this.recognition) {
            try {
                this.recognition.stop();
                return true;
            } catch (e) {
                console.error('停止语音识别失败:', e);
                return false;
            }
        }
        return false;
    }

    abort() {
        if (this.recognition) {
            try {
                this.recognition.abort();
                this.isListening = false;
                return true;
            } catch (e) {
                console.error('中止语音识别失败:', e);
                return false;
            }
        }
        return false;
    }

    setLanguage(lang) {
        this.language = lang;
        if (this.recognition) {
            this.recognition.lang = lang;
        }
    }

    isAvailable() {
        return this.isSupported;
    }

    static isAvailable() {
        return 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
    }

    static getSupportedLanguages() {
        return [
            { code: 'zh-CN', name: '中文 (简体)', native: '中文 (简体)' },
            { code: 'zh-TW', name: '中文 (繁体)', native: '中文 (繁體)' },
            { code: 'en-US', name: 'English (US)', native: 'English' },
            { code: 'en-GB', name: 'English (UK)', native: 'English (UK)' },
            { code: 'ja-JP', name: '日本語', native: '日本語' },
            { code: 'ko-KR', name: '한국어', native: '한국어' },
            { code: 'fr-FR', name: 'Français', native: 'Français' },
            { code: 'de-DE', name: 'Deutsch', native: 'Deutsch' },
            { code: 'es-ES', name: 'Español', native: 'Español' },
            { code: 'ru-RU', name: 'Русский', native: 'Русский' },
        ];
    }

    static getLanguageByCode(code) {
        const languages = this.getSupportedLanguages();
        return languages.find(lang => lang.code === code) || languages[0];
    }
}

/**
 * 语音合成工具 - Text-to-Speech Module
 * 使用 Web Speech Synthesis API 实现语音朗读功能
 */
class VoiceOutput {
    constructor(options = {}) {
        this.synth = window.speechSynthesis;
        this.voices = [];
        this.voice = null;
        this.rate = options.rate || 1.0;
        this.pitch = options.pitch || 1.0;
        this.volume = options.volume || 1.0;
        this.language = options.language || 'zh-CN';
        this.onStart = options.onStart || (() => {});
        this.onEnd = options.onEnd || (() => {});
        this.onError = options.onError || ((error) => console.error('语音合成错误:', error));

        this.init();
    }

    init() {
        if (!('speechSynthesis' in window)) {
            console.warn('当前浏览器不支持 Web Speech Synthesis API');
            this.isSupported = false;
            return;
        }

        this.isSupported = true;

        const loadVoices = () => {
            this.voices = this.synth.getVoices();
            this.voice = this.voices.find(v => v.lang.startsWith(this.language.slice(0, 2))) || this.voices[0];
        };

        loadVoices();

        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = loadVoices;
        }
    }

    speak(text, options = {}) {
        if (!this.isSupported) {
            this.onError({
                error: 'not-supported',
                message: '当前浏览器不支持语音合成功能'
            });
            return false;
        }

        this.stop();

        const utterance = new SpeechSynthesisUtterance(text);

        if (options.voice) {
            utterance.voice = options.voice;
        } else if (this.voice) {
            utterance.voice = this.voice;
        }

        utterance.rate = options.rate || this.rate;
        utterance.pitch = options.pitch || this.pitch;
        utterance.volume = options.volume || this.volume;
        utterance.lang = options.language || this.language;

        utterance.onstart = () => this.onStart();
        utterance.onend = () => this.onEnd();
        utterance.onerror = (event) => {
            if (event.error !== 'canceled' && event.error !== 'interrupted') {
                this.onError({
                    error: event.error,
                    message: '语音合成出错'
                });
            }
        };

        this.synth.speak(utterance);
        return true;
    }

    pause() {
        if (this.synth) {
            this.synth.pause();
        }
    }

    resume() {
        if (this.synth) {
            this.synth.resume();
        }
    }

    stop() {
        if (this.synth) {
            this.synth.cancel();
        }
    }

    isSpeaking() {
        return this.synth ? this.synth.speaking : false;
    }

    setVoice(voice) {
        this.voice = voice;
    }

    setRate(rate) {
        this.rate = Math.max(0.1, Math.min(10, rate));
    }

    setPitch(pitch) {
        this.pitch = Math.max(0, Math.min(2, pitch));
    }

    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
    }

    setLanguage(lang) {
        this.language = lang;
        this.voice = this.voices.find(v => v.lang.startsWith(lang.slice(0, 2))) || this.voice;
    }

    getVoices() {
        return this.voices;
    }

    isAvailable() {
        return this.isSupported;
    }
}

/**
 * 录音工具 - Audio Recording Module
 * 使用 MediaRecorder API 实现录音功能
 */
class AudioRecorder {
    constructor(options = {}) {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.stream = null;
        this.isRecording = false;
        this.onDataAvailable = options.onDataAvailable || ((blob) => console.log('录音数据:', blob));
        this.onError = options.onError || ((error) => console.error('录音错误:', error));
        this.onStart = options.onStart || (() => {});
        this.onStop = options.onStop || (() => {});
    }

    async start(options = {}) {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                audio: options.audio || true
            });

            this.audioChunks = [];
            this.mediaRecorder = new MediaRecorder(this.stream, {
                mimeType: options.mimeType || 'audio/webm'
            });

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                const blob = new Blob(this.audioChunks, {
                    type: this.mediaRecorder.mimeType
                });
                this.onDataAvailable(blob);
            };

            this.mediaRecorder.onerror = (event) => {
                this.onError({
                    error: 'recording-error',
                    message: '录音过程中出错'
                });
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            this.onStart();

            return true;
        } catch (error) {
            let errorMessage = '无法访问麦克风';

            if (error.name === 'NotAllowedError') {
                errorMessage = '麦克风访问被拒绝，请在浏览器设置中允许访问';
            } else if (error.name === 'NotFoundError') {
                errorMessage = '未找到麦克风设备';
            } else if (error.name === 'NotReadableError') {
                errorMessage = '麦克风正在被其他程序使用';
            }

            this.onError({
                error: error.name,
                message: errorMessage
            });

            return false;
        }
    }

    stop() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;

            if (this.stream) {
                this.stream.getTracks().forEach(track => track.stop());
            }

            this.onStop();
            return true;
        }
        return false;
    }

    pause() {
        if (this.mediaRecorder && this.isRecording && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.pause();
            return true;
        }
        return false;
    }

    resume() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'paused') {
            this.mediaRecorder.resume();
            return true;
        }
        return false;
    }

    isRecording() {
        return this.isRecording;
    }

    static isSupported() {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    }

    static async getDevices() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            return devices.filter(device => device.kind === 'audioinput');
        } catch (error) {
            return [];
        }
    }
}

/**
 * 音频波形可视化 - Audio Waveform Visualizer
 */
class AudioVisualizer {
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.analyser = null;
        this.dataArray = null;
        this.animationId = null;
        this.options = {
            barColor: options.barColor || '#3b82f6',
            backgroundColor: options.backgroundColor || 'transparent',
            barWidth: options.barWidth || 3,
            barGap: options.barGap || 2,
            minHeight: options.minHeight || 2,
            maxHeight: options.maxHeight || 100,
            ...options
        };
    }

    connect(stream) {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioContext.createMediaStreamSource(stream);

        this.analyser = audioContext.createAnalyser();
        this.analyser.fftSize = 256;

        source.connect(this.analyser);

        this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
        this.draw();
    }

    draw() {
        if (!this.analyser) return;

        this.analyser.getByteFrequencyData(this.dataArray);

        this.ctx.fillStyle = this.options.backgroundColor;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        const barCount = Math.floor(this.canvas.width / (this.options.barWidth + this.options.barGap));
        const step = Math.floor(this.dataArray.length / barCount);

        for (let i = 0; i < barCount; i++) {
            const value = this.dataArray[i * step];
            const height = Math.max(
                this.options.minHeight,
                (value / 255) * this.options.maxHeight
            );

            const x = i * (this.options.barWidth + this.options.barGap);
            const y = (this.canvas.height - height) / 2;

            this.ctx.fillStyle = this.options.barColor;
            this.ctx.fillRect(x, y, this.options.barWidth, height);
        }

        this.animationId = requestAnimationFrame(() => this.draw());
    }

    stop() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }

    setColors(barColor, backgroundColor) {
        this.options.barColor = barColor;
        this.options.backgroundColor = backgroundColor;
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { VoiceInput, VoiceOutput, AudioRecorder, AudioVisualizer };
}
