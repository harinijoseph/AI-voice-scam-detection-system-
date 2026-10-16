import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Navigation from './components/Navigation';
import Compartment1_Scanner from './components/Compartment1_Scanner';
import Compartment2_Physics from './components/Compartment2_Physics';
import Compartment3_Conversation from './components/Compartment3_Conversation';
import BenchmarkPage from './components/BenchmarkPage';
import SidebarFusionControl from './components/SidebarFusionControl';

export default function App() {
  // Top-level page state: 'forensics' (Scanner & Forensics Hub) | 'benchmarks' (Dedicated Benchmark Lab)
  const [activePage, setActivePage] = useState('forensics');
  
  // Compartment tab within 'forensics' page: 'scanner' | 'physics' | 'conversation'
  const [activeTab, setActiveTab] = useState('scanner');
  
  const [backendConnected, setBackendConnected] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [presets, setPresets] = useState([]);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [wAcoustic, setWAcoustic] = useState(0.50);

  // 1. Initial Health & Presets fetch
  useEffect(() => {
    checkHealth();
    loadPresets();
  }, []);

  const checkHealth = async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        setBackendConnected(true);
      } else {
        setBackendConnected(false);
      }
    } catch {
      setBackendConnected(false);
    }
  };

  const loadPresets = async () => {
    try {
      const res = await fetch('/api/presets');
      if (res.ok) {
        const data = await res.json();
        setPresets(data.presets || []);
        // Automatically load first preset to arm dashboard
        if (data.presets && data.presets.length > 0) {
          selectPreset(data.presets[1] || data.presets[0]); // Start on Grandparent Trap for dramatic demonstration
        }
      }
    } catch (e) {
      console.error("Error loading presets:", e);
    }
  };

  // 2. Select Preset handler
  const selectPreset = async (preset) => {
    if (!preset) return;
    setIsAnalyzing(true);
    try {
      const audioResp = await fetch(preset.audio_url);
      const audioBlob = await audioResp.blob();
      const file = new File([audioBlob], `${preset.id}.wav`, { type: 'audio/wav' });
      await analyzeAudioFile(file, preset.transcript || "", false);
    } catch (err) {
      console.error("Preset selection failed:", err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 3. Main Audio Analysis handler (Upload or Mic)
  const analyzeAudioFile = async (file, transcript = "", isMicrophone = false) => {
    setIsAnalyzing(true);
    try {
      const formData = new FormData();
      formData.append('audio_file', file);
      formData.append('transcript', transcript);
      formData.append('w_acoustic', wAcoustic.toString());
      formData.append('is_microphone', isMicrophone ? 'true' : 'false');

      const res = await fetch('/api/analyze/audio', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || "Audio analysis failed");
      }

      const data = await res.json();
      setAnalysisResult(data);
    } catch (error) {
      console.error("Analysis execution error:", error);
      alert(`Audio analysis notice: ${error.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 4. Direct Dataset Sample Analysis handler
  const handleAnalyzeDatasetSample = async (sample) => {
    if (!sample || !sample.filename) return;
    setIsAnalyzing(true);
    setActivePage('forensics');
    setActiveTab('scanner');

    try {
      const res = await fetch('/api/analyze/dataset-sample', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category: sample.category || 'human',
          filename: sample.filename,
          w_acoustic: wAcoustic,
          transcript: ""
        })
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || "Dataset sample analysis failed");
      }

      const data = await res.json();
      setAnalysisResult(data);
    } catch (err) {
      console.error("Dataset analysis error:", err);
      alert(`Dataset analysis notice: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 5. Load Random Dataset Sample handler
  const handleLoadRandomDatasetSample = async (category = 'human') => {
    setIsAnalyzing(true);
    try {
      const res = await fetch(`/api/presets/dataset-random?category=${category}`);
      if (!res.ok) throw new Error("Failed to fetch random dataset preset");
      const presetData = await res.json();

      await handleAnalyzeDatasetSample({
        category: presetData.category,
        filename: presetData.filename,
        name: presetData.name,
        threat_level: presetData.threat_level
      });
    } catch (err) {
      console.error("Random dataset sample loading failed:", err);
      alert(`Dataset sampling notice: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 6. Update Transcript handler
  const handleUpdateTranscript = async (audioFilename, newTranscript) => {
    setIsAnalyzing(true);
    try {
      const res = await fetch('/api/analyze/transcript', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          audio_filename: audioFilename,
          transcript: newTranscript,
          w_acoustic: wAcoustic
        })
      });

      if (res.ok) {
        const data = await res.json();
        setAnalysisResult(prev => ({
          ...prev,
          overall_risk_score: data.overall_risk_score,
          risk_category: data.risk_category,
          risk_color: data.risk_color,
          verdict: data.verdict,
          content_result: data.content_result,
          engine_breakdown: data.engine_breakdown,
          transcript: data.transcript
        }));
      }
    } catch (err) {
      console.error("Transcript update error:", err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 7. Reset Audio Signal handler
  const handleResetSignal = () => {
    if (presets.length > 0) {
      selectPreset(presets[0]); // Reset to Legitimate Family Call
    }
  };

  return (
    <div className="min-h-screen bg-[#f8f9fa] flex flex-col font-sans text-slate-900 antialiased">
      {/* Top Academic Header with Page Switcher */}
      <Header 
        backendConnected={backendConnected} 
        isAnalyzing={isAnalyzing} 
        activePage={activePage}
        setActivePage={setActivePage}
      />

      {/* Sub-Navigation Bar: Active only on Voice Forensics Page */}
      {activePage === 'forensics' && (
        <Navigation activeTab={activeTab} setActiveTab={setActiveTab} />
      )}

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 lg:p-8">
        {/* PAGE 1: Voice Forensics & Scanner Hub */}
        {activePage === 'forensics' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Main Compartment View (9 Cols) */}
            <div className="lg:col-span-8 xl:col-span-9">
              {activeTab === 'scanner' && (
                <Compartment1_Scanner
                  analysisResult={analysisResult}
                  onAnalyzeAudio={analyzeAudioFile}
                  isAnalyzing={isAnalyzing}
                  presets={presets}
                  onSelectPreset={selectPreset}
                  onLoadRandomDatasetSample={handleLoadRandomDatasetSample}
                  wAcoustic={wAcoustic}
                  setWAcoustic={setWAcoustic}
                />
              )}

              {activeTab === 'physics' && (
                <Compartment2_Physics
                  analysisResult={analysisResult}
                />
              )}

              {activeTab === 'conversation' && (
                <Compartment3_Conversation
                  analysisResult={analysisResult}
                  onUpdateTranscript={handleUpdateTranscript}
                  isAnalyzing={isAnalyzing}
                />
              )}
            </div>

            {/* Right Sidebar Control Unit (3 Cols) */}
            <div className="lg:col-span-4 xl:col-span-3 sticky top-20 space-y-6">
              <SidebarFusionControl
                analysisResult={analysisResult}
                wAcoustic={wAcoustic}
                setWAcoustic={setWAcoustic}
                onResetSignal={handleResetSignal}
              />
            </div>
          </div>
        )}

        {/* PAGE 2: Benchmark Lab & Dataset Evaluation (Totally Separate Full Page) */}
        {activePage === 'benchmarks' && (
          <BenchmarkPage 
            onInspectInScanner={handleAnalyzeDatasetSample}
          />
        )}
      </main>

      {/* Academic Footer */}
      <footer className="w-full bg-white border-t border-slate-200 py-6 px-6 mt-12 text-center text-xs text-slate-500 font-mono">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div>
            <b>VoxSentinel AI Defense Framework</b> — Conformer Acoustic Forensics & Behavioral Intent Engine
          </div>
          <div>
            FastAPI Backend • React 19 Frontend • human-nonhuman Verified Corpus
          </div>
        </div>
      </footer>
    </div>
  );
}
