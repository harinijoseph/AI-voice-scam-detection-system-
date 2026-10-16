import React, { useState, useEffect } from 'react';
import { MessageSquareWarning, RefreshCw, AlertCircle, ShieldCheck, Tag, Layers } from 'lucide-react';

export default function Compartment3_Conversation({ analysisResult, onUpdateTranscript, isAnalyzing }) {
  const contentResult = analysisResult?.content_result || {};
  const [editedTranscript, setEditedTranscript] = useState(contentResult.transcript || "");

  useEffect(() => {
    setEditedTranscript(contentResult.transcript || "");
  }, [contentResult.transcript]);

  const detectedStage = contentResult.detected_stage || "General Dialogue / Initial Statement";
  const tactics = contentResult.detected_tactics || [];
  const category = contentResult.category || "Authentic / Normal Dialogue";
  const flagged = contentResult.flagged_phrases || [];

  const rawActiveStages = contentResult.active_stages;
  const activeStages = Array.isArray(rawActiveStages) && rawActiveStages.length > 0
    ? rawActiveStages
    : (detectedStage && !detectedStage.includes("General Dialogue") ? [detectedStage] : []);

  const stage1Active = activeStages.some(s => s.includes("Stage 1"));
  const stage2Active = activeStages.some(s => s.includes("Stage 2"));
  const stage3Active = activeStages.some(s => s.includes("Stage 3"));
  const stage4Active = activeStages.some(s => s.includes("Stage 4"));

  const handleReAnalyze = () => {
    if (analysisResult?.audio_filename) {
      onUpdateTranscript(analysisResult.audio_filename, editedTranscript);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header card */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="p-1.5 rounded-md bg-orange-100 text-orange-700">
              <MessageSquareWarning className="w-4 h-4" />
            </span>
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500">
              Compartment 03: Conversational Intent
            </span>
          </div>
          <h2 className="text-xl font-black text-slate-900 tracking-tight">
            Conversation & Scam Words Analyzer
          </h2>
          <p className="text-sm text-slate-600 max-w-3xl leading-relaxed">
            Voice cloning is merely the disguise; coercive social engineering is the weapon. 
            This compartment tracks conversational intent, parses social pressure tactics, and maps the 4-stage scam progression.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Transcript & Tactics (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Transcript Box */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-bold text-slate-900">
                Spoken Call Transcript
              </label>
              <span className="text-[11px] font-mono text-slate-400">
                Editable for Testing
              </span>
            </div>

            <textarea
              value={editedTranscript}
              onChange={(e) => setEditedTranscript(e.target.value)}
              rows={5}
              placeholder="Spoken words will automatically appear here via Speech-to-Text..."
              className="w-full text-xs md:text-sm p-3.5 rounded-lg border border-slate-300 bg-slate-50 focus:bg-white focus:border-orange-500 focus:ring-1 focus:ring-orange-500 outline-none transition-all leading-relaxed"
            />

            <button
              onClick={handleReAnalyze}
              disabled={isAnalyzing || !analysisResult?.audio_filename}
              className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold font-mono transition-all cursor-pointer shadow-xs disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isAnalyzing ? 'animate-spin' : ''}`} />
              <span>Re-Evaluate Behavioral Intent</span>
            </button>
          </div>

          {/* Detected Tactics & Taxonomy */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
            <div>
              <div className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500 mb-2">
                Detected Coercive Tactics
              </div>
              <div className="flex flex-wrap gap-1.5">
                {tactics.length > 0 ? (
                  tactics.map((t, idx) => (
                    <span 
                      key={idx}
                      className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-md bg-red-100 text-red-800 text-xs font-bold"
                    >
                      <AlertCircle className="w-3 h-3" />
                      <span>{t}</span>
                    </span>
                  ))
                ) : (
                  <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-md bg-emerald-100 text-emerald-800 text-xs font-bold">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>No Coercive Tactics Detected</span>
                  </span>
                )}
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100">
              <div className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500 mb-1">
                Scam Category Classification
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 font-mono font-bold text-sm text-orange-600">
                {category}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: 4-Stage Social Engineering Funnel (7 Cols) */}
        <div className="lg:col-span-7 bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-5">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Layers className="w-4 h-4 text-orange-600" />
              <span>The 4-Stage Social Engineering Funnel (Plain English)</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Scammers systematically guide victims through 4 psychological phases to bypass logical scrutiny:
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            {/* Stage 1 */}
            <div className={`p-4 rounded-xl border transition-all ${
              stage1Active 
                ? 'bg-orange-50 border-orange-400 shadow-sm ring-2 ring-orange-400/20' 
                : 'bg-slate-50/70 border-slate-200 opacity-80'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono font-black uppercase text-slate-400">
                  01 / STAGE 1
                </span>
                {stage1Active && (
                  <span className="text-[10px] font-mono px-2 py-0.5 bg-orange-600 text-white rounded font-bold uppercase">
                    ACTIVE
                  </span>
                )}
              </div>
              <h4 className="text-sm font-bold text-slate-900">
                Greeting & Fake Persona
              </h4>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                Caller establishes false intimacy or authority (grandchild, bank security, law enforcement officer).
              </p>
            </div>

            {/* Stage 2 */}
            <div className={`p-4 rounded-xl border transition-all ${
              stage2Active 
                ? 'bg-orange-50 border-orange-400 shadow-sm ring-2 ring-orange-400/20' 
                : 'bg-slate-50/70 border-slate-200 opacity-80'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono font-black uppercase text-slate-400">
                  02 / STAGE 2
                </span>
                {stage2Active && (
                  <span className="text-[10px] font-mono px-2 py-0.5 bg-orange-600 text-white rounded font-bold uppercase">
                    ACTIVE
                  </span>
                )}
              </div>
              <h4 className="text-sm font-bold text-slate-900">
                Creating Panic (Crisis)
              </h4>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                Fabricates an emergency (car accident, arrest, frozen account) to trigger amygdala hijack and disable critical reasoning.
              </p>
            </div>

            {/* Stage 3 */}
            <div className={`p-4 rounded-xl border transition-all ${
              stage3Active 
                ? 'bg-orange-50 border-orange-400 shadow-sm ring-2 ring-orange-400/20' 
                : 'bg-slate-50/70 border-slate-200 opacity-80'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono font-black uppercase text-slate-400">
                  03 / STAGE 3
                </span>
                {stage3Active && (
                  <span className="text-[10px] font-mono px-2 py-0.5 bg-orange-600 text-white rounded font-bold uppercase">
                    ACTIVE
                  </span>
                )}
              </div>
              <h4 className="text-sm font-bold text-slate-900">
                Artificial Urgency
              </h4>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                Commands victim not to hang up and demands compliance within minutes to prevent conferring with friends or family.
              </p>
            </div>

            {/* Stage 4 */}
            <div className={`p-4 rounded-xl border transition-all ${
              stage4Active 
                ? 'bg-orange-50 border-orange-400 shadow-sm ring-2 ring-orange-400/20' 
                : 'bg-slate-50/70 border-slate-200 opacity-80'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono font-black uppercase text-slate-400">
                  04 / STAGE 4
                </span>
                {stage4Active && (
                  <span className="text-[10px] font-mono px-2 py-0.5 bg-orange-600 text-white rounded font-bold uppercase">
                    ACTIVE
                  </span>
                )}
              </div>
              <h4 className="text-sm font-bold text-slate-900">
                Coercive Demands
              </h4>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                Demands untraceable funds (wire transfer, cryptocurrency, gift cards) or harvests one-time authentication passcodes (OTP).
              </p>
            </div>
          </div>

          {/* Current Stage Badge Banner */}
          <div className="p-4 rounded-lg bg-slate-900 text-white flex items-center justify-between">
            <div>
              <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                Current Funnel State (Peak Phase)
              </div>
              <div className="text-sm font-bold font-mono text-orange-400 mt-0.5">
                {detectedStage}
              </div>
              {activeStages.length > 0 && (
                <div className="text-[11px] font-mono text-slate-400 mt-1">
                  Active Stages: {activeStages.map(s => s.split(':')[0]).join(' + ')}
                </div>
              )}
            </div>
            <span className="text-xs text-slate-400 max-w-xs text-right">
              Matched against 4-stage social engineering intent trajectory.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
