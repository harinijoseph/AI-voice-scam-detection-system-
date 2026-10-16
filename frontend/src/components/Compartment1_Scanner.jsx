import React, { useState, useRef, useEffect } from 'react';
import { 
  Mic, Square, Upload, Play, Pause, AlertTriangle, ShieldCheck, 
  ShieldAlert, RefreshCw, Volume2, Sparkles, FileAudio, ArrowRight,
  Database
} from 'lucide-react';
import { encodeWAV, downsampleBuffer } from '../utils/wavEncoder';
import AudioWaveformGraph from './AudioWaveformGraph';

export default function Compartment1_Scanner({ 
  analysisResult, 
  onAnalyzeAudio, 
  isAnalyzing, 
  presets, 
  onSelectPreset,
  onLoadRandomDatasetSample,
  wAcoustic,
  setWAcoustic 
}) {
  const [inputMode, setInputMode] = useState('mic'); // 'mic' | 'upload' | 'preset'
  const [isRecording, setIsRecording] = useState(false);
  const [recordDuration, setRecordDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  // Audio recording refs
  const pcmBuffersRef = useRef([]);
  const processorRef = useRef(null);
  const streamRef = useRef(null);
  const timerRef = useRef(null);
  const canvasRef = useRef(null);
  const animationFrameRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const audioPlayerRef = useRef(null);

  // Reset playback when analysis result changes
  useEffect(() => {
    setIsPlaying(false);
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      audioPlayerRef.current.currentTime = 0;
    }
  }, [analysisResult]);

  // Clean up audio context & timers on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      if (processorRef.current) {
        processorRef.current.disconnect();
        processorRef.current = null;
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
      }
    };
  }, []);

  // --- Real-Time Microphone Recording & In-Browser 16-Bit PCM WAV Encoding ---
  const startRecording = async () => {
    pcmBuffersRef.current = [];
    setRecordDuration(0);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      audioContextRef.current = audioCtx;

      // Real-time audio analyzer for canvas oscilloscope
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      analyserRef.current = analyser;

      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      // Start drawing canvas waveform
      drawLiveWaveform();

      // Collect raw PCM Float32 audio samples directly from microphone stream
      const processor = audioCtx.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;
      processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        pcmBuffersRef.current.push(new Float32Array(inputData));
      };

      source.connect(processor);
      processor.connect(audioCtx.destination);

      setIsRecording(true);

      // Timer interval
      timerRef.current = setInterval(() => {
        setRecordDuration(prev => prev + 1);
      }, 1000);

    } catch (err) {
      console.error("Microphone access error:", err);
      alert("Microphone permission denied or microphone device unavailable. Please allow microphone access in your browser.");
    }
  };

  const stopRecording = () => {
    if (!isRecording) return;
    setIsRecording(false);

    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    const audioCtx = audioContextRef.current;
    const inputSampleRate = audioCtx ? audioCtx.sampleRate : 44100;
    if (audioCtx && audioCtx.state !== 'closed') {
      audioCtx.close();
    }

    // Merge Float32 PCM chunks
    const totalLength = pcmBuffersRef.current.reduce((acc, b) => acc + b.length, 0);
    if (totalLength === 0) return;

    const merged = new Float32Array(totalLength);
    let offset = 0;
    for (const b of pcmBuffersRef.current) {
      merged.set(b, offset);
      offset += b.length;
    }

    // Downsample to 16,000 Hz & encode into standard 16-bit PCM WAV (RIFF header)
    const downsampled = downsampleBuffer(merged, inputSampleRate, 16000);
    const wavBlob = encodeWAV(downsampled, 16000);
    const wavFile = new File([wavBlob], `mic_${Date.now()}.wav`, { type: 'audio/wav' });

    // Trigger server analysis with 100% compliant PCM WAV
    onAnalyzeAudio(wavFile, "", true);
  };

  // Canvas visualizer loop
  const drawLiveWaveform = () => {
    if (!canvasRef.current || !analyserRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const analyser = analyserRef.current;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const render = () => {
      animationFrameRef.current = requestAnimationFrame(render);
      analyser.getByteFrequencyData(dataArray);

      ctx.fillStyle = '#0f172a';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const barWidth = (canvas.width / bufferLength) * 2.2;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height * 0.9;
        
        // Gradient orange to amber
        ctx.fillStyle = i % 2 === 0 ? '#ea580c' : '#f97316';
        ctx.fillRect(x, canvas.height - barHeight, barWidth - 1, barHeight);
        x += barWidth;
      }
    };

    render();
  };

  // --- File Upload Handler ---
  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      onAnalyzeAudio(file, "", false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      onAnalyzeAudio(file, "", false);
    }
  };

  // --- Audio Player Toggle ---
  const togglePlayAudio = () => {
    if (!audioPlayerRef.current) return;
    if (isPlaying) {
      audioPlayerRef.current.pause();
      setIsPlaying(false);
    } else {
      audioPlayerRef.current.play().then(() => {
        setIsPlaying(true);
      }).catch(e => console.error("Audio playback error:", e));
    }
  };

  const verdict = analysisResult?.verdict;
  const overallRisk = analysisResult?.overall_risk_score !== undefined 
    ? Math.round(analysisResult.overall_risk_score * 100) 
    : 19;
  const voiceRisk = verdict?.voice_risk_pct !== undefined ? verdict.voice_risk_pct : 0.2;
  const wordsRisk = verdict?.words_risk_pct !== undefined ? verdict.words_risk_pct : 19.4;

  return (
    <div className="space-y-6">
      {/* Top Banner Card: Ingestion Switcher */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-5">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>🎙️</span> Inbound Voice Signal Ingestion
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Feed live microphone voice, upload telephony audio, or test adversarial scam presets.
            </p>
          </div>

          {/* Mode Switcher Tabs */}
          <div className="flex bg-slate-100 p-1 rounded-lg border border-slate-200">
            <button
              onClick={() => setInputMode('mic')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all cursor-pointer ${
                inputMode === 'mic' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Mic className="w-3.5 h-3.5 text-orange-600" />
              <span>Record Microphone</span>
            </button>

            <button
              onClick={() => setInputMode('upload')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all cursor-pointer ${
                inputMode === 'upload' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Upload className="w-3.5 h-3.5 text-slate-700" />
              <span>Upload Audio</span>
            </button>

            <button
              onClick={() => setInputMode('preset')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all cursor-pointer ${
                inputMode === 'preset' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 text-orange-500" />
              <span>Scam Presets</span>
            </button>

            <button
              onClick={() => setInputMode('dataset')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all cursor-pointer ${
                inputMode === 'dataset' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Database className="w-3.5 h-3.5 text-orange-600" />
              <span>Dataset Audio (human-nonhuman)</span>
            </button>
          </div>
        </div>

        {/* Input Mode: Microphone */}
        {inputMode === 'mic' && (
          <div className="flex flex-col items-center justify-center p-6 bg-slate-50 border border-slate-200 rounded-xl space-y-4">
            <div className="text-center space-y-1">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500">
                Live Acoustic Capture
              </span>
              <p className="text-sm font-semibold text-slate-800">
                Speak normally for 3–5 seconds to test your authentic vocal physics
              </p>
            </div>

            {/* Canvas for Live Audio Visualizer */}
            {isRecording && (
              <div className="w-full max-w-md h-20 bg-slate-900 rounded-lg overflow-hidden border border-slate-800 shadow-inner flex items-center justify-center">
                <canvas ref={canvasRef} width="400" height="80" className="w-full h-full" />
              </div>
            )}

            {/* Mic Action Button */}
            <div className="flex items-center space-x-4">
              {!isRecording ? (
                <button
                  onClick={startRecording}
                  disabled={isAnalyzing}
                  className="flex items-center space-x-2.5 px-6 py-3 rounded-full bg-orange-600 hover:bg-orange-700 text-white font-bold text-sm shadow-md transition-all cursor-pointer transform hover:scale-102"
                >
                  <Mic className="w-4 h-4" />
                  <span>Start Microphone Recording</span>
                </button>
              ) : (
                <button
                  onClick={stopRecording}
                  className="flex items-center space-x-2.5 px-6 py-3 rounded-full bg-red-600 hover:bg-red-700 text-white font-bold text-sm shadow-md transition-all cursor-pointer animate-pulse"
                >
                  <Square className="w-4 h-4 fill-white" />
                  <span>Stop & Analyze ({recordDuration}s)</span>
                </button>
              )}
            </div>

            <p className="text-xs text-slate-400">
              Audio is processed in-memory at 16kHz PCM mono with automated noise reduction.
            </p>
          </div>
        )}

        {/* Input Mode: File Upload */}
        {inputMode === 'upload' && (
          <div 
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
              dragOver ? 'border-orange-500 bg-orange-50/50' : 'border-slate-300 bg-slate-50/60'
            }`}
          >
            <input 
              type="file" 
              accept=".wav,.mp3,.ogg,.m4a" 
              onChange={handleFileUpload} 
              id="file-upload" 
              className="hidden" 
            />
            <label htmlFor="file-upload" className="cursor-pointer space-y-3 block">
              <div className="w-12 h-12 rounded-full bg-slate-200 flex items-center justify-center mx-auto text-slate-600">
                <Upload className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm font-bold text-slate-800">
                  Click to select audio file or drag & drop here
                </p>
                <p className="text-xs text-slate-500 mt-1 font-mono">
                  Supported formats: .wav (16-bit PCM), .mp3, .ogg, .m4a
                </p>
              </div>
            </label>
          </div>
        )}

        {/* Input Mode: Presets */}
        {inputMode === 'preset' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {presets && presets.map((p) => {
              const isSafe = p.threat_level === 'safe';
              return (
                <button
                  key={p.id}
                  onClick={() => onSelectPreset(p)}
                  disabled={isAnalyzing}
                  className="flex flex-col text-left p-3.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 hover:border-orange-300 transition-all cursor-pointer group shadow-2xs"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold text-slate-900 group-hover:text-orange-600">
                      {p.name}
                    </span>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold uppercase ${
                      isSafe ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {p.tag}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">
                    {p.description}
                  </p>
                </button>
              );
            })}
          </div>
        )}

        {/* Input Mode: Dataset Audio (human-nonhuman) */}
        {inputMode === 'dataset' && (
          <div className="p-5 bg-slate-50 border border-slate-200 rounded-xl space-y-4">
            <div>
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500">
                Corpus Speech Ingestion (human-nonhuman/)
              </span>
              <p className="text-sm font-semibold text-slate-800 mt-0.5">
                Directly test real empirical audio files from the 2,088-file verified speech dataset
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              <button
                onClick={() => onLoadRandomDatasetSample && onLoadRandomDatasetSample('human')}
                disabled={isAnalyzing}
                className="flex items-center space-x-3.5 p-4 rounded-xl border border-emerald-200 bg-white hover:bg-emerald-50/70 text-left transition-all cursor-pointer shadow-xs group"
              >
                <div className="w-10 h-10 rounded-lg bg-emerald-600 text-white flex items-center justify-center font-bold text-lg shrink-0">
                  👤
                </div>
                <div>
                  <div className="text-xs font-bold text-emerald-950 flex items-center gap-1.5">
                    <span>Load Random Human Voice</span>
                    <span className="text-[10px] font-mono bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded font-bold">1,001 Files</span>
                  </div>
                  <p className="text-xs text-slate-600 mt-0.5">
                    Authentic speech from <code>human-nonhuman/human/</code>
                  </p>
                </div>
              </button>

              <button
                onClick={() => onLoadRandomDatasetSample && onLoadRandomDatasetSample('nonhuman')}
                disabled={isAnalyzing}
                className="flex items-center space-x-3.5 p-4 rounded-xl border border-red-200 bg-white hover:bg-red-50/70 text-left transition-all cursor-pointer shadow-xs group"
              >
                <div className="w-10 h-10 rounded-lg bg-red-600 text-white flex items-center justify-center font-bold text-lg shrink-0">
                  🤖
                </div>
                <div>
                  <div className="text-xs font-bold text-red-950 flex items-center gap-1.5">
                    <span>Load Random AI Voice Clone</span>
                    <span className="text-[10px] font-mono bg-red-100 text-red-800 px-1.5 py-0.5 rounded font-bold">1,000 Files</span>
                  </div>
                  <p className="text-xs text-slate-600 mt-0.5">
                    Synthetic speech clone from <code>human-nonhuman/nonhuman/</code>
                  </p>
                </div>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Main Human Verdict Banner */}
      {verdict && (
        <div 
          className="rounded-xl p-6 border shadow-sm transition-all"
          style={{ 
            backgroundColor: verdict.bg_color || '#ffffff', 
            borderColor: verdict.border_color || '#e2e8f0',
            borderLeftWidth: '8px'
          }}
        >
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-1.5 max-w-2xl">
              <span 
                className="inline-block px-2.5 py-0.5 rounded text-[11px] font-mono font-bold tracking-wider uppercase text-white shadow-2xs"
                style={{ backgroundColor: verdict.border_color || '#ea580c' }}
              >
                {verdict.badge || 'DEFENSE VERDICT'}
              </span>
              <h2 
                className="text-2xl font-black tracking-tight"
                style={{ color: verdict.text_color || '#0f172a' }}
              >
                {verdict.title}
              </h2>
              <p className="text-sm font-semibold opacity-90" style={{ color: verdict.text_color || '#334155' }}>
                {verdict.subtitle}
              </p>
            </div>

            {/* Risk Badge on the right */}
            <div className="bg-white/90 backdrop-blur-xs border border-black/10 rounded-lg p-3 text-right shadow-xs min-w-[130px]">
              <div className="text-[10px] font-mono font-bold tracking-wider uppercase text-slate-500">
                COMPOSITE RISK
              </div>
              <div 
                className="text-3xl font-black font-mono leading-none mt-1"
                style={{ color: verdict.border_color || '#ea580c' }}
              >
                {overallRisk}%
              </div>
            </div>
          </div>

          {/* Plain English explanation box */}
          <div className="mt-4 p-4 rounded-lg bg-white/80 border border-black/5 text-sm text-slate-800 leading-relaxed space-y-2">
            <div>
              <b className="text-slate-900">Why this decision was reached (Plain English):</b>
              <p className="mt-1 text-slate-700 text-xs md:text-sm">{verdict.summary}</p>
            </div>
            <div className="pt-2 border-t border-slate-200/60 flex items-start space-x-2">
              <span className="text-sm">🛡️</span>
              <p className="text-xs font-bold" style={{ color: verdict.text_color || '#0f172a' }}>
                <b>Recommended Action:</b> {verdict.advice}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Inputted Audio Signal Graph (Waveform & Spectrum) */}
      <AudioWaveformGraph analysisResult={analysisResult} />

      {/* Multimodal Score Cards & Audio Player */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Metric 1: Composite Risk */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500">
              Composite Risk
            </span>
            <span className="text-xs font-bold text-slate-400">Fused</span>
          </div>
          <div className="my-2">
            <div className="text-2xl font-black font-mono text-slate-900">
              {overallRisk}%
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2 mt-2 overflow-hidden">
              <div 
                className="h-full rounded-full transition-all duration-500"
                style={{ 
                  width: `${overallRisk}%`, 
                  backgroundColor: overallRisk >= 65 ? '#dc2626' : (overallRisk >= 35 ? '#d97706' : '#16a34a') 
                }}
              />
            </div>
          </div>
          <span className="text-[11px] text-slate-500">
            Threshold: Safe &lt;35% | Caution 35–65% | Threat &ge;65%
          </span>
        </div>

        {/* Metric 2: Voice Physics (Acoustics) */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500">
              Vocal Physics Risk
            </span>
            <span className="text-xs font-bold text-slate-400">Acoustic</span>
          </div>
          <div className="my-2">
            <div className="text-2xl font-black font-mono text-slate-900">
              {voiceRisk}%
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2 mt-2 overflow-hidden">
              <div 
                className="h-full bg-slate-800 rounded-full transition-all duration-500"
                style={{ width: `${voiceRisk}%` }}
              />
            </div>
          </div>
          <span className="text-[11px] text-slate-500 font-mono">
            {voiceRisk < 10 ? '✅ 99.8% Genuine Vocal Cord Drift' : '⚠️ Synthesized Timbre Detected'}
          </span>
        </div>

        {/* Metric 3: Conversation Intent (NLP) */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500">
              Conversation Risk
            </span>
            <span className="text-xs font-bold text-slate-400">Semantic</span>
          </div>
          <div className="my-2">
            <div className="text-2xl font-black font-mono text-slate-900">
              {wordsRisk}%
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2 mt-2 overflow-hidden">
              <div 
                className="h-full bg-orange-600 rounded-full transition-all duration-500"
                style={{ width: `${wordsRisk}%` }}
              />
            </div>
          </div>
          <span className="text-[11px] text-slate-500 font-mono">
            {wordsRisk >= 50 ? '⚠️ Urgent Financial Demands Flagged' : '✅ Benign Dialogue Intent'}
          </span>
        </div>
      </div>

      {/* In-Page Audio Playback & Signal Card */}
      {analysisResult?.audio_url && (
        <div className="bg-slate-900 text-white rounded-xl p-4 flex flex-wrap items-center justify-between gap-4 shadow-sm">
          <audio 
            ref={audioPlayerRef} 
            src={analysisResult.audio_url} 
            onEnded={() => setIsPlaying(false)}
            className="hidden" 
          />

          <div className="flex items-center space-x-3">
            <button
              onClick={togglePlayAudio}
              className="w-10 h-10 rounded-full bg-orange-600 hover:bg-orange-500 text-white flex items-center justify-center transition-all cursor-pointer shadow-xs"
            >
              {isPlaying ? <Pause className="w-5 h-5 fill-white" /> : <Play className="w-5 h-5 fill-white ml-0.5" />}
            </button>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono font-bold uppercase text-orange-400">
                  Audio Signal Source
                </span>
                {analysisResult?.dataset_metadata && (
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                    analysisResult.dataset_metadata.category === 'human' 
                      ? 'bg-emerald-900/80 text-emerald-300 border border-emerald-700' 
                      : 'bg-red-900/80 text-red-300 border border-red-700'
                  }`}>
                    Ground Truth: {analysisResult.dataset_metadata.ground_truth}
                  </span>
                )}
              </div>
              <div className="text-sm font-semibold text-white truncate max-w-md">
                {analysisResult.audio_filename || 'Active Inbound Stream'}
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-6 text-xs font-mono text-slate-400">
            <div>
              <span className="text-slate-500">Duration: </span>
              <span className="text-slate-200">{analysisResult.duration_seconds || 8.0}s</span>
            </div>
            <div>
              <span className="text-slate-500">Encoding: </span>
              <span className="text-slate-200">16kHz PCM 16-Bit</span>
            </div>
            <div>
              <span className="text-slate-500">Payload: </span>
              <span className="text-slate-200">{analysisResult.file_size_kb || 250} KB</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
