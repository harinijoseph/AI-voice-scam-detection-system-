import React, { useState } from 'react';
import { Activity, BarChart2, Volume2, Info, Eye } from 'lucide-react';

export default function AudioWaveformGraph({ analysisResult }) {
  const [activeGraphTab, setActiveGraphTab] = useState('waveform'); // 'waveform' | 'spectrum'

  const waveformData = analysisResult?.waveform_data || [];
  const spectrumData = analysisResult?.spectrum_data || [];
  const duration = analysisResult?.duration_seconds || 8.0;

  // SVG dimensions for Waveform
  const svgWidth = 720;
  const svgHeight = 160;
  const padding = { top: 15, right: 25, bottom: 25, left: 35 };

  // Generate smooth Waveform SVG path
  const graphWidth = svgWidth - padding.left - padding.right;
  const graphHeight = svgHeight - padding.top - padding.bottom;
  const midY = padding.top + graphHeight / 2;

  let upperPath = "";
  let lowerPath = "";

  if (waveformData.length > 0) {
    waveformData.forEach((pt, idx) => {
      const x = padding.left + (idx / (waveformData.length - 1)) * graphWidth;
      const amp = Math.min(1.0, Math.max(0.04, pt.amplitude || pt.rms || 0.1));
      const yUp = midY - amp * (graphHeight / 2 * 0.9);
      const yDown = midY + amp * (graphHeight / 2 * 0.9);

      if (idx === 0) {
        upperPath = `M ${x} ${yUp}`;
        lowerPath = `M ${x} ${yDown}`;
      } else {
        upperPath += ` L ${x} ${yUp}`;
        lowerPath += ` L ${x} ${yDown}`;
      }
    });
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
      {/* Header & Graph Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          <span className="p-1.5 rounded-md bg-orange-100 text-orange-700">
            <Activity className="w-4 h-4" />
          </span>
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
              <span>Inputted Audio Signal Graph</span>
              <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                {duration}s Duration
              </span>
            </h3>
            <p className="text-[11px] text-slate-500 font-mono">
              Real-time physical amplitude envelope & FFT frequency power distribution
            </p>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-mono">
          <button
            onClick={() => setActiveGraphTab('waveform')}
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-md font-bold transition-all cursor-pointer ${
              activeGraphTab === 'waveform' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Activity className="w-3.5 h-3.5 text-orange-600" />
            <span>Waveform (Time)</span>
          </button>

          <button
            onClick={() => setActiveGraphTab('spectrum')}
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-md font-bold transition-all cursor-pointer ${
              activeGraphTab === 'spectrum' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BarChart2 className="w-3.5 h-3.5 text-slate-700" />
            <span>Power Spectrum (FFT)</span>
          </button>
        </div>
      </div>

      {/* VIEW 1: Waveform (Amplitude vs Time) */}
      {activeGraphTab === 'waveform' && (
        <div className="space-y-2">
          <div className="w-full bg-slate-950 rounded-xl p-3 border border-slate-800 shadow-inner overflow-hidden">
            <svg 
              viewBox={`0 0 ${svgWidth} ${svgHeight}`} 
              className="w-full h-36 md:h-44"
              preserveAspectRatio="none"
            >
              {/* Background gridlines */}
              <line x1={padding.left} y1={midY} x2={svgWidth - padding.right} y2={midY} stroke="#334155" strokeDasharray="3 3" />
              <line x1={padding.left} y1={padding.top} x2={padding.left} y2={svgHeight - padding.bottom} stroke="#475569" />
              <line x1={padding.left} y1={svgHeight - padding.bottom} x2={svgWidth - padding.right} y2={svgHeight - padding.bottom} stroke="#475569" />

              {/* Time tick labels */}
              {[0, 0.25, 0.5, 0.75, 1.0].map((frac, idx) => {
                const x = padding.left + frac * graphWidth;
                const timeSec = (frac * duration).toFixed(1);
                return (
                  <g key={idx}>
                    <line x1={x} y1={svgHeight - padding.bottom} x2={x} y2={svgHeight - padding.bottom + 4} stroke="#64748b" />
                    <text x={x} y={svgHeight - padding.bottom + 16} fill="#94a3b8" fontSize="10" fontFamily="monospace" textAnchor="middle">
                      {timeSec}s
                    </text>
                  </g>
                );
              })}

              {/* Amplitude envelope visualization */}
              {waveformData.length > 0 ? (
                <>
                  {/* Mirror Waveform Area */}
                  {waveformData.map((pt, idx) => {
                    const x = padding.left + (idx / (waveformData.length - 1)) * graphWidth;
                    const amp = Math.min(1.0, Math.max(0.04, pt.amplitude || pt.rms || 0.1));
                    const barHeight = amp * (graphHeight * 0.85);
                    const y = midY - barHeight / 2;
                    return (
                      <rect
                        key={idx}
                        x={x - 1}
                        y={y}
                        width="2.5"
                        height={barHeight}
                        fill={idx % 2 === 0 ? "#ea580c" : "#f97316"}
                        rx="1"
                        opacity={0.88}
                      />
                    );
                  })}
                  {/* Zero axis centerline */}
                  <line x1={padding.left} y1={midY} x2={svgWidth - padding.right} y2={midY} stroke="#ea580c" strokeWidth="0.8" opacity="0.4" />
                </>
              ) : (
                <text x={svgWidth / 2} y={midY} fill="#64748b" fontSize="12" fontFamily="monospace" textAnchor="middle">
                  Awaiting audio signal ingestion...
                </text>
              )}
            </svg>
          </div>

          <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 px-1">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-orange-600 inline-block"></span>
              <span>16-Bit PCM Oscilloscope Trace</span>
            </span>
            <span>Sampling Rate: 16,000 Hz Mono</span>
          </div>
        </div>
      )}

      {/* VIEW 2: Power Spectrum Bins (FFT Frequency Bands) */}
      {activeGraphTab === 'spectrum' && (
        <div className="space-y-2">
          <div className="w-full bg-slate-950 rounded-xl p-4 border border-slate-800 shadow-inner overflow-hidden">
            <div className="h-36 md:h-44 flex items-end justify-between gap-1 pt-6 px-2">
              {spectrumData.length > 0 ? (
                spectrumData.map((bin, idx) => {
                  const isLow = bin.freq <= 300;
                  const isMid = bin.freq > 300 && bin.freq <= 3400;
                  const color = isLow ? "bg-emerald-500" : (isMid ? "bg-orange-500" : "bg-red-500");
                  return (
                    <div 
                      key={idx} 
                      className="flex-1 flex flex-col items-center justify-end h-full group relative"
                    >
                      {/* Tooltip on hover */}
                      <div className="absolute -top-7 hidden group-hover:flex bg-slate-800 text-white text-[9px] font-mono px-1.5 py-0.5 rounded shadow whitespace-nowrap z-10 border border-slate-700">
                        {bin.freq} Hz ({bin.norm_pct}%)
                      </div>
                      <div 
                        className={`w-full rounded-t-xs transition-all duration-300 ${color}`}
                        style={{ height: `${Math.max(4, bin.norm_pct || 10)}%` }}
                      />
                    </div>
                  );
                })
              ) : (
                <div className="w-full h-full flex items-center justify-center text-slate-500 text-xs font-mono">
                  Loading vocal tract spectrum...
                </div>
              )}
            </div>

            {/* Frequency Axis Markings */}
            <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 mt-2 border-t border-slate-800 pt-1.5">
              <span>80 Hz (Pitch Base)</span>
              <span>300 Hz</span>
              <span>1,000 Hz (Formants)</span>
              <span>3,400 Hz (Phone Line Cutoff)</span>
              <span>8,000 Hz (Vocoder Band)</span>
            </div>
          </div>

          {/* Forensic Legend */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px] font-mono pt-1">
            <div className="p-2 rounded-lg bg-emerald-50/60 border border-emerald-200 text-emerald-900">
              <span className="font-bold text-emerald-700">80–300 Hz:</span> Vocal Cord F₀ Fundamental
            </div>
            <div className="p-2 rounded-lg bg-orange-50/60 border border-orange-200 text-orange-900">
              <span className="font-bold text-orange-700">300–3,400 Hz:</span> Vowel Formants & Telephony
            </div>
            <div className="p-2 rounded-lg bg-red-50/60 border border-red-200 text-red-900">
              <span className="font-bold text-red-700">3,400–8,000 Hz:</span> Vocoder Artifacts Band
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
