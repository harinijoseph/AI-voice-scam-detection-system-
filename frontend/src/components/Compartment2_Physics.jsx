import React, { useState } from 'react';
import { Microscope, Activity, HelpCircle, CheckCircle2, AlertTriangle, Cpu } from 'lucide-react';

export default function Compartment2_Physics({ analysisResult }) {
  const [hoveredPoint, setHoveredPoint] = useState(null);

  const pitchPoints = analysisResult?.pitch_points || [];
  const telemetryRows = analysisResult?.telemetry_rows || [];

  // Calculate SVG dimensions for the pitch contour
  const svgWidth = 700;
  const svgHeight = 220;
  const padding = { top: 20, right: 30, bottom: 40, left: 50 };

  const validPitches = pitchPoints.filter(p => p.pitch > 0);
  const maxTime = pitchPoints.length > 0 ? pitchPoints[pitchPoints.length - 1].time : 8;
  const minPitch = validPitches.length > 0 ? Math.max(50, Math.min(...validPitches.map(p => p.pitch)) - 20) : 80;
  const maxPitch = validPitches.length > 0 ? Math.max(...validPitches.map(p => p.pitch)) + 30 : 260;

  const getX = (t) => padding.left + (t / (maxTime || 1)) * (svgWidth - padding.left - padding.right);
  const getY = (hz) => {
    if (!hz || hz <= 0) return svgHeight - padding.bottom;
    const norm = (hz - minPitch) / (maxPitch - minPitch || 1);
    return (svgHeight - padding.bottom) - norm * (svgHeight - padding.top - padding.bottom);
  };

  // Generate SVG path string
  let pathD = "";
  pitchPoints.forEach((p, idx) => {
    if (p.is_voiced && p.pitch > 0) {
      const x = getX(p.time);
      const y = getY(p.pitch);
      if (!pathD) {
        pathD = `M ${x} ${y}`;
      } else {
        pathD += ` L ${x} ${y}`;
      }
    }
  });

  return (
    <div className="space-y-6">
      {/* Header card */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="p-1.5 rounded-md bg-orange-100 text-orange-700">
                <Microscope className="w-4 h-4" />
              </span>
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500">
                Compartment 02: Signal Acoustics
              </span>
            </div>
            <h2 className="text-xl font-black text-slate-900 tracking-tight">
              Vocal Cord Physics & Neural Vocoder Telemetry
            </h2>
            <p className="text-sm text-slate-600 max-w-3xl leading-relaxed">
              Why humans cannot hear deepfakes: Neural voice synthesizers mimic superficial vocal timbre, 
              but fail to recreate involuntary physiological micro-tremors, continuous mucosal phase flow, and respiratory energy drift.
            </p>
          </div>
        </div>

        {/* Plain English Guide Callout */}
        <div className="mt-5 p-4 rounded-lg bg-orange-50/70 border border-orange-200/80 text-xs md:text-sm text-slate-800 leading-relaxed flex items-start space-x-3">
          <span className="text-base mt-0.5">💡</span>
          <div>
            <b className="text-slate-900 font-bold">The Science Explained Simply:</b>
            <p className="mt-0.5 text-slate-700">
              When a genuine human speaks, involuntary contractions of the vocal fold tissues cause minute, chaotic fluctuations 
              in pitch (<b>Jitter</b>) and amplitude (<b>Shimmer</b>). Neural vocoders (HiFi-GAN, WaveNet) produce mathematically quantized, 
              unnaturally rigid pitch lines and high-frequency phase discontinuities.
            </p>
          </div>
        </div>
      </div>

      {/* Figure 1: Fundamental Frequency (Pitch Contour) */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Activity className="w-4 h-4 text-orange-600" />
              <span>Figure 1: Fundamental Frequency Contour (F₀ Track)</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5 font-mono">
              Algorithm: Probabilistic YIN (pYIN) with Voiced/Unvoiced Viterbi Path Decoding
            </p>
          </div>

          <div className="flex items-center space-x-4 text-xs font-mono">
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-1 bg-orange-600 rounded"></span>
              <span className="text-slate-600">Voiced Pitch Track</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-1 bg-slate-300 rounded"></span>
              <span className="text-slate-400">Unvoiced / Silence</span>
            </div>
          </div>
        </div>

        {/* Interactive SVG Pitch Chart */}
        <div className="relative w-full overflow-x-auto bg-slate-950 rounded-lg p-2 border border-slate-800 shadow-inner">
          <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-auto min-w-[550px]">
            {/* Grid lines */}
            {[0.25, 0.5, 0.75].map((ratio, i) => {
              const y = padding.top + ratio * (svgHeight - padding.top - padding.bottom);
              const hz = Math.round(maxPitch - ratio * (maxPitch - minPitch));
              return (
                <g key={i}>
                  <line 
                    x1={padding.left} 
                    y1={y} 
                    x2={svgWidth - padding.right} 
                    y2={y} 
                    stroke="#1e293b" 
                    strokeDasharray="4 4" 
                  />
                  <text x={padding.left - 8} y={y + 3} fill="#64748b" fontSize="10" fontFamily="monospace" textAnchor="end">
                    {hz}Hz
                  </text>
                </g>
              );
            })}

            {/* Time labels */}
            {[0, 0.25, 0.5, 0.75, 1.0].map((ratio, i) => {
              const t = (ratio * maxTime).toFixed(1);
              const x = getX(ratio * maxTime);
              return (
                <text key={i} x={x} y={svgHeight - 12} fill="#64748b" fontSize="10" fontFamily="monospace" textAnchor="middle">
                  {t}s
                </text>
              );
            })}

            {/* Pitch path */}
            {pathD && (
              <path 
                d={pathD} 
                fill="none" 
                stroke="#ea580c" 
                strokeWidth="2.5" 
                strokeLinecap="round" 
                strokeLinejoin="round" 
              />
            )}

            {/* Hover points */}
            {pitchPoints.map((p, idx) => {
              if (!p.is_voiced || p.pitch <= 0) return null;
              const x = getX(p.time);
              const y = getY(p.pitch);
              return (
                <circle
                  key={idx}
                  cx={x}
                  cy={y}
                  r="3"
                  className="fill-orange-400 hover:fill-white cursor-pointer transition-all"
                  onMouseEnter={() => setHoveredPoint(p)}
                  onMouseLeave={() => setHoveredPoint(null)}
                />
              );
            })}
          </svg>

          {/* Hover tooltip card */}
          {hoveredPoint && (
            <div className="absolute top-4 right-4 bg-slate-900/90 border border-slate-700 p-2.5 rounded text-xs font-mono text-white shadow-md">
              <div>Time: <span className="text-orange-400">{hoveredPoint.time}s</span></div>
              <div>Frequency: <span className="text-orange-400">{hoveredPoint.pitch} Hz</span></div>
            </div>
          )}
        </div>
      </div>

      {/* Human-Readable Forensic Telemetry Table */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
        <div>
          <h3 className="text-sm font-bold text-slate-900">
            Empirical Forensic Telemetry Table
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Physical parameters extracted directly from the inbound audio and compared against empirical benchmarks.
          </p>
        </div>

        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="w-full text-left text-xs md:text-sm">
            <thead className="bg-slate-100/80 text-slate-700 font-mono text-[11px] uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-3 px-4 font-bold">Forensic Metric</th>
                <th className="py-3 px-4 font-bold">What It Means (Plain English)</th>
                <th className="py-3 px-4 font-bold">Measured Value</th>
                <th className="py-3 px-4 font-bold">Normal Human Range</th>
                <th className="py-3 px-4 font-bold">Cloned AI Range</th>
                <th className="py-3 px-4 font-bold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {telemetryRows.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-slate-900">
                    {row.name}
                  </td>
                  <td className="py-3.5 px-4 text-xs text-slate-600 max-w-xs leading-relaxed">
                    {row.meaning}
                  </td>
                  <td className="py-3.5 px-4 font-mono font-bold text-slate-800">
                    {row.value}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-xs text-emerald-700 font-semibold">
                    {row.human_range}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-xs text-red-700 font-semibold">
                    {row.ai_range}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold ${
                      row.is_safe ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {row.is_safe ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertTriangle className="w-3.5 h-3.5" />}
                      <span>{row.status}</span>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Conformer Neural Architecture Card */}
      <div className="bg-slate-900 text-white border border-slate-800 rounded-xl p-6 shadow-sm space-y-3">
        <div className="flex items-center space-x-2 text-orange-400">
          <Cpu className="w-4 h-4" />
          <span className="text-xs font-mono font-bold tracking-wider uppercase">
            Acoustic Conformer Neural Architecture
          </span>
        </div>
        <p className="text-xs md:text-sm text-slate-300 leading-relaxed">
          VoxSentinel deploys an <b>AcousticConformer</b> deep neural network trained on 400-dimensional spectral embeddings. 
          By interleaving Multi-Head Self-Attention (MHSA) with depthwise convolutions, the network captures both global utterance-level cadence 
          and localized vocoder artifacts in under 180 milliseconds.
        </p>
      </div>
    </div>
  );
}
