import React from 'react';
import { Sliders, RefreshCw, Volume2, Shield, Info } from 'lucide-react';

export default function SidebarFusionControl({ 
  analysisResult, 
  wAcoustic, 
  setWAcoustic, 
  onResetSignal 
}) {
  const wContent = (1.0 - wAcoustic).toFixed(2);

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-5">
      {/* Title */}
      <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
        <Sliders className="w-4 h-4 text-orange-600" />
        <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
          Forensic Fusion Balance
        </h3>
      </div>

      {/* Active Audio Signal Card */}
      <div className="p-3.5 rounded-lg bg-slate-900 text-white space-y-1.5 shadow-xs">
        <div className="text-[10px] font-mono text-orange-400 font-bold uppercase tracking-wider">
          Active Inbound Signal
        </div>
        <div className="text-xs font-bold truncate">
          {analysisResult?.audio_filename || "Awaiting Input Signal"}
        </div>
        <div className="text-[11px] font-mono text-slate-400 flex items-center justify-between pt-1">
          <span>{analysisResult?.duration_seconds ? `${analysisResult.duration_seconds}s` : '0.0s'}</span>
          <span>16kHz PCM</span>
        </div>
      </div>

      {/* Fusion Slider */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-bold text-slate-800">
          <span>Acoustic Forensics</span>
          <span className="font-mono text-orange-600">{wAcoustic.toFixed(2)}</span>
        </div>
        
        <input 
          type="range" 
          min="0.0" 
          max="1.0" 
          step="0.05"
          value={wAcoustic}
          onChange={(e) => setWAcoustic(parseFloat(e.target.value))}
          className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-orange-600"
        />

        <div className="flex items-center justify-between text-[11px] font-mono text-slate-500">
          <span>Words: {wContent}</span>
          <span>Voice: {wAcoustic.toFixed(2)}</span>
        </div>
      </div>

      {/* Reset Button */}
      <button
        onClick={onResetSignal}
        className="w-full flex items-center justify-center space-x-2 py-2 px-3 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-bold font-mono transition-all cursor-pointer shadow-2xs"
      >
        <RefreshCw className="w-3.5 h-3.5 text-slate-500" />
        <span>Reset Signal & Presets</span>
      </button>

      {/* Testing Tip */}
      <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 text-[11px] text-slate-600 leading-relaxed space-y-1">
        <div className="flex items-center space-x-1.5 text-slate-900 font-bold">
          <Info className="w-3.5 h-3.5 text-orange-600" />
          <span>Quick Testing Tip</span>
        </div>
        <p>
          Click <b>Record Microphone</b> in Compartment 1, speak for 3–5 seconds, and watch the real neural Conformer verify your natural pitch jitter.
        </p>
      </div>
    </div>
  );
}
