import React from 'react';
import { Shield, Radio, Activity, BarChart3, RadioTower } from 'lucide-react';

export default function Header({ backendConnected, isAnalyzing, activePage, setActivePage }) {
  return (
    <header className="w-full bg-white border-b border-slate-200 px-4 md:px-6 py-3.5 shadow-xs sticky top-0 z-50">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
        {/* Brand identity */}
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-lg bg-slate-900 flex items-center justify-center text-white shadow-xs shrink-0">
            <Shield className="w-5 h-5 text-orange-500" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-mono font-bold tracking-wider uppercase text-slate-500">
                VoxSentinel AI Defense Framework
              </span>
              <span className="text-slate-300">•</span>
              <span className="text-xs font-mono font-semibold text-slate-500">
                Multimodal Forensics
              </span>
            </div>
            <h1 className="text-base md:text-lg font-black text-slate-900 tracking-tight flex items-center gap-2">
              Zero-Shot Synthetic Voice Scam Defense
            </h1>
          </div>
        </div>

        {/* Top-Level Page Switcher */}
        <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200">
          <button
            onClick={() => setActivePage('forensics')}
            className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              activePage === 'forensics'
                ? 'bg-slate-900 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Shield className={`w-3.5 h-3.5 ${activePage === 'forensics' ? 'text-orange-400' : 'text-slate-500'}`} />
            <span>Voice Forensics & Scanner</span>
          </button>

          <button
            onClick={() => setActivePage('benchmarks')}
            className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              activePage === 'benchmarks'
                ? 'bg-slate-900 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BarChart3 className={`w-3.5 h-3.5 ${activePage === 'benchmarks' ? 'text-orange-400' : 'text-slate-500'}`} />
            <span>Benchmark Lab & Dataset</span>
          </button>
        </div>

        {/* Live system status badges */}
        <div className="flex items-center space-x-2.5">
          {/* Analysis indicator */}
          {isAnalyzing && (
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-md bg-orange-50 border border-orange-200 text-orange-700 text-xs font-mono font-semibold animate-pulse">
              <Activity className="w-3.5 h-3.5 animate-spin" />
              <span>SCANNING...</span>
            </div>
          )}

          {/* Backend Connection badge */}
          <div className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-md border text-xs font-mono font-semibold ${
            backendConnected 
              ? 'bg-slate-50 border-slate-200 text-slate-700' 
              : 'bg-red-50 border-red-200 text-red-700'
          }`}>
            <span className={`w-2 h-2 rounded-full ${backendConnected ? 'bg-emerald-500 radar-dot' : 'bg-red-500'}`}></span>
            <span>{backendConnected ? 'ONLINE' : 'CONNECTING'}</span>
          </div>

          {/* System Armed Radar Badge */}
          <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800 text-white text-xs font-mono font-bold">
            <Radio className="w-3.5 h-3.5 text-orange-400 animate-pulse" />
            <span>ARMED</span>
          </div>
        </div>
      </div>
    </header>
  );
}
