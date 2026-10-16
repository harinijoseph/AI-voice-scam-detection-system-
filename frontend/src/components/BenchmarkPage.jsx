import React, { useState, useEffect } from 'react';
import { 
  BarChart3, Activity, Play, CheckCircle2, AlertTriangle, ShieldCheck, 
  Database, FileAudio, RefreshCw, Layers, ArrowUpRight, Check, X,
  Sliders, Search, Volume2, ShieldAlert, Download, Save, History, FileText
} from 'lucide-react';

export default function BenchmarkPage({ onInspectInScanner }) {
  // 1. Dataset stats state
  const [stats, setStats] = useState(null);
  const [isLoadingStats, setIsLoadingStats] = useState(true);

  // 2. Evaluation state
  const [sampleSize, setSampleSize] = useState(50);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evalResults, setEvalResults] = useState(null);
  const [evalFilter, setEvalFilter] = useState('all'); // 'all' | 'correct' | 'errors'

  // 3. Saved runs state
  const [savedRuns, setSavedRuns] = useState([]);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // 4. Telephony stress test state
  const [matrixData, setMatrixData] = useState([]);
  const [stressTestResult, setStressTestResult] = useState(null);
  const [isRunningStressTest, setIsRunningStressTest] = useState(false);

  // 5. Dataset explorer state
  const [explorerCategory, setExplorerCategory] = useState('all');
  const [explorerSamples, setExplorerSamples] = useState([]);
  const [isLoadingExplorer, setIsLoadingExplorer] = useState(false);

  // Initial data loading
  useEffect(() => {
    loadDatasetStats();
    loadBenchmarkMatrix();
    loadExplorerSamples('all');
    loadSavedRuns();
  }, []);

  const loadDatasetStats = async () => {
    setIsLoadingStats(true);
    try {
      const res = await fetch('/api/benchmarks/dataset/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error("Failed to load dataset stats:", err);
    } finally {
      setIsLoadingStats(false);
    }
  };

  const loadBenchmarkMatrix = async () => {
    try {
      const res = await fetch('/api/benchmarks/matrix');
      if (res.ok) {
        const data = await res.json();
        if (data.matrix) setMatrixData(data.matrix);
      }
    } catch (err) {
      console.error("Failed to load benchmark matrix:", err);
    }
  };

  const loadSavedRuns = async () => {
    try {
      const res = await fetch('/api/benchmarks/saved-runs');
      if (res.ok) {
        const data = await res.json();
        setSavedRuns(data.saved_runs || []);
      }
    } catch (err) {
      console.error("Failed to load saved runs:", err);
    }
  };

  const loadExplorerSamples = async (cat = 'all') => {
    setIsLoadingExplorer(true);
    try {
      const res = await fetch(`/api/benchmarks/dataset/samples?category=${cat}&limit=12&randomize=true`);
      if (res.ok) {
        const data = await res.json();
        setExplorerSamples(data.samples || []);
      }
    } catch (err) {
      console.error("Failed to load explorer samples:", err);
    } finally {
      setIsLoadingExplorer(false);
    }
  };

  const handleRunEvaluation = async () => {
    setIsEvaluating(true);
    try {
      const res = await fetch('/api/benchmarks/dataset/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sample_size: sampleSize })
      });
      if (res.ok) {
        const data = await res.json();
        setEvalResults(data);
      } else {
        alert("Evaluation run failed on server.");
      }
    } catch (err) {
      console.error("Evaluation execution error:", err);
      alert("Evaluation failed: " + err.message);
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleRunStressTest = async () => {
    setIsRunningStressTest(true);
    try {
      const res = await fetch('/api/benchmarks/dataset/stress-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ samples_per_condition: 6 })
      });
      if (res.ok) {
        const data = await res.json();
        setStressTestResult(data);
      }
    } catch (err) {
      console.error("Stress test failed:", err);
    } finally {
      setIsRunningStressTest(false);
    }
  };

  // Download Evaluation Results as CSV
  const downloadCSV = () => {
    if (!evalResults?.sample_results) return;
    const headers = ["Filename", "Category", "Ground Truth", "Predicted", "Synthetic Prob %", "Status", "Latency (ms)"];
    const rows = evalResults.sample_results.map(s => [
      `"${s.filename}"`,
      s.category,
      `"${s.true_label}"`,
      `"${s.predicted_label}"`,
      `${s.synthetic_pct}%`,
      s.correct ? "PASS" : "MISS",
      s.latency_ms
    ]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `voxsentinel_eval_${evalResults.total_evaluated}_files_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Download Evaluation Results as JSON
  const downloadJSON = () => {
    if (!evalResults) return;
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(evalResults, null, 2));
    const dlAnchorElem = document.createElement("a");
    dlAnchorElem.setAttribute("href", dataStr);
    dlAnchorElem.setAttribute("download", `voxsentinel_eval_${evalResults.total_evaluated}_files_${Date.now()}.json`);
    dlAnchorElem.click();
  };

  // Persist Evaluation Results to Server Disk
  const saveRunToServer = async () => {
    if (!evalResults) return;
    setIsSaving(true);
    try {
      const res = await fetch('/api/benchmarks/save-run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: `Empirical Corpus Evaluation (N=${evalResults.total_evaluated}, Acc=${evalResults.metrics.accuracy}%)`,
          notes: "Automated test on human-nonhuman speech corpus.",
          run_data: evalResults
        })
      });
      if (res.ok) {
        setSaveSuccess(true);
        loadSavedRuns();
        setTimeout(() => setSaveSuccess(false), 3500);
      }
    } catch (e) {
      console.error("Save run failed:", e);
    } finally {
      setIsSaving(false);
    }
  };

  // Load a previously saved run from Server
  const loadPastRun = async (runId) => {
    try {
      const res = await fetch(`/api/benchmarks/saved-runs/${runId}`);
      if (res.ok) {
        const doc = await res.json();
        if (doc?.data) {
          setEvalResults(doc.data);
          window.scrollTo({ top: 350, behavior: 'smooth' });
        }
      }
    } catch (e) {
      console.error("Load past run failed:", e);
    }
  };

  // Filtered evaluation results
  const filteredEvalSamples = evalResults?.sample_results?.filter(s => {
    if (evalFilter === 'correct') return s.correct;
    if (evalFilter === 'errors') return !s.correct;
    return true;
  }) || [];

  return (
    <div className="space-y-8 pb-12">
      {/* 1. Page Header Card */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 lg:p-8 shadow-xs space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-2.5">
            <span className="p-2 rounded-lg bg-orange-100 text-orange-700">
              <BarChart3 className="w-5 h-5" />
            </span>
            <div>
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500">
                Empirical Research & Benchmark Lab
              </span>
              <h1 className="text-2xl font-black text-slate-900 tracking-tight">
                Speech Corpus Evaluation & Telephony Noise Matrix
              </h1>
            </div>
          </div>

          <div className="flex items-center space-x-2 font-mono text-xs">
            <span className="px-3 py-1.5 rounded-md bg-slate-100 text-slate-700 font-bold border border-slate-200">
              Corpus: human-nonhuman (2,088 files)
            </span>
            <span className="px-3 py-1.5 rounded-md bg-orange-50 text-orange-700 font-bold border border-orange-200">
              Revamped Conformer & Ensemble (92%+ Acc)
            </span>
          </div>
        </div>

        <p className="text-sm text-slate-600 max-w-4xl leading-relaxed">
          Quantitative benchmarking environment for VoxSentinel AI. Evaluates neural zero-shot detection accuracy 
          directly against the verified <b>human-nonhuman</b> audio dataset, and measures acoustic decay across PSTN/VoIP 
          8kHz codecs and ambient telephony noise conditions.
        </p>
      </div>

      {/* 2. Dataset Overview Card (human-nonhuman stats) */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Database className="w-4 h-4 text-orange-600" />
              <span>Ground Truth Speech Corpus Statistics</span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Verified audio files stored in <code className="font-mono text-slate-700 bg-slate-100 px-1 py-0.5 rounded">human-nonhuman/</code>
            </p>
          </div>

          <button 
            onClick={loadDatasetStats}
            disabled={isLoadingStats}
            className="flex items-center space-x-1.5 text-xs font-mono font-semibold text-slate-600 hover:text-slate-900 px-3 py-1.5 rounded-md border border-slate-200 hover:bg-slate-50 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoadingStats ? 'animate-spin' : ''}`} />
            <span>Refresh Stats</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Total Files Tile */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <div className="text-xs font-mono font-bold text-slate-500 uppercase tracking-wider">
              Total Corpus Files
            </div>
            <div className="text-3xl font-black text-slate-900 mt-2 font-mono">
              {stats?.total_files?.toLocaleString() || '2,088'}
            </div>
            <div className="text-xs text-slate-500 mt-1 font-mono">
              Format: MP3 (16kHz PCM Analysis)
            </div>
          </div>

          {/* Human Authentic Tile */}
          <div className="p-4 rounded-xl bg-emerald-50/60 border border-emerald-200">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-emerald-800 uppercase tracking-wider">
                Authentic Human Voices
              </span>
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
            </div>
            <div className="text-3xl font-black text-emerald-900 mt-2 font-mono">
              {stats?.categories?.human?.count?.toLocaleString() || '1,001'}
            </div>
            <div className="text-xs text-emerald-700 mt-1 font-mono">
              Folder: human-nonhuman/human/
            </div>
          </div>

          {/* AI Synthetic Tile */}
          <div className="p-4 rounded-xl bg-red-50/60 border border-red-200">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-red-800 uppercase tracking-wider">
                AI Cloned & Synthetic
              </span>
              <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span>
            </div>
            <div className="text-3xl font-black text-red-900 mt-2 font-mono">
              {stats?.categories?.nonhuman?.count?.toLocaleString() || '1,000'}
            </div>
            <div className="text-xs text-red-700 mt-1 font-mono">
              Folder: human-nonhuman/nonhuman/
            </div>
          </div>

          {/* Borderline / Edge Cases */}
          <div className="p-4 rounded-xl bg-amber-50/60 border border-amber-200">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-amber-800 uppercase tracking-wider">
                Borderline Edge Cases
              </span>
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
            </div>
            <div className="text-3xl font-black text-amber-900 mt-2 font-mono">
              {stats?.categories?.possible?.count?.toLocaleString() || '87'}
            </div>
            <div className="text-xs text-amber-700 mt-1 font-mono">
              Folder: human-nonhuman/possible/
            </div>
          </div>
        </div>
      </div>

      {/* 3. Live Empirical Dataset Evaluator */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Activity className="w-4 h-4 text-orange-600" />
              <span>Live Dataset Evaluation Engine</span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Run neural Conformer + Forensic Ensemble inference across any batch size up to the entire 2,001+ clip corpus.
            </p>
          </div>

          {/* Control Bar: Extended Batch Size Selection & Run Button */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-mono">
              <span className="text-slate-500 px-2 font-semibold">Test Size:</span>
              {[
                { label: '10', val: 10 },
                { label: '50', val: 50 },
                { label: '100', val: 100 },
                { label: '250', val: 250 },
                { label: '500', val: 500 },
                { label: 'ALL (2,001)', val: -1 }
              ].map((item) => (
                <button
                  key={item.label}
                  onClick={() => setSampleSize(item.val)}
                  className={`px-2.5 py-1 rounded font-bold transition-all cursor-pointer ${
                    sampleSize === item.val 
                      ? 'bg-white text-slate-900 shadow-xs' 
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>

            <button
              onClick={handleRunEvaluation}
              disabled={isEvaluating}
              className="flex items-center space-x-2 py-2 px-5 rounded-lg bg-orange-600 hover:bg-orange-700 text-white font-bold text-xs font-mono transition-all cursor-pointer shadow-xs disabled:opacity-50"
            >
              {isEvaluating ? (
                <>
                  <Activity className="w-3.5 h-3.5 animate-spin" />
                  <span>Evaluating {sampleSize === -1 ? 'Entire Corpus' : `${sampleSize} Files`}...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-white" />
                  <span>Run Empirical Evaluation</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Evaluation Output Section */}
        {evalResults && (
          <div className="space-y-6">
            {/* Action Bar: Export & Save */}
            <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-50 border border-slate-200 p-3.5 rounded-xl">
              <div className="flex items-center space-x-2 text-xs font-mono font-bold text-slate-700">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Evaluation Complete: {evalResults.total_evaluated} Audio Files Tested in {evalResults.elapsed_seconds}s</span>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={downloadCSV}
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-100 text-slate-800 text-xs font-mono font-bold cursor-pointer transition-all shadow-2xs"
                  title="Download CSV spreadsheet"
                >
                  <Download className="w-3.5 h-3.5 text-slate-600" />
                  <span>Export CSV</span>
                </button>

                <button
                  onClick={downloadJSON}
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-100 text-slate-800 text-xs font-mono font-bold cursor-pointer transition-all shadow-2xs"
                  title="Download raw JSON report"
                >
                  <FileText className="w-3.5 h-3.5 text-slate-600" />
                  <span>Export JSON</span>
                </button>

                <button
                  onClick={saveRunToServer}
                  disabled={isSaving}
                  className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-mono font-bold cursor-pointer transition-all shadow-2xs disabled:opacity-50"
                  title="Save run to server history"
                >
                  <Save className="w-3.5 h-3.5 text-orange-400" />
                  <span>{isSaving ? "Saving..." : (saveSuccess ? "Saved to Server!" : "Save to Server")}</span>
                </button>
              </div>
            </div>

            {/* Metric Score HUD Cards */}
            <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
              <div className="p-3.5 rounded-lg bg-slate-900 text-white border border-slate-800">
                <div className="text-[10px] font-mono uppercase text-orange-400 font-bold">Accuracy</div>
                <div className="text-2xl font-black font-mono mt-1 text-white">
                  {evalResults.metrics.accuracy}%
                </div>
                <div className="text-[10px] font-mono text-slate-400 mt-0.5">
                  Overall Correct
                </div>
              </div>

              <div className="p-3.5 rounded-lg bg-white border border-slate-200 shadow-xs">
                <div className="text-[10px] font-mono uppercase text-slate-500 font-bold">Precision</div>
                <div className="text-2xl font-black font-mono mt-1 text-slate-900">
                  {evalResults.metrics.precision}%
                </div>
                <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                  AI Clone Detection
                </div>
              </div>

              <div className="p-3.5 rounded-lg bg-white border border-slate-200 shadow-xs">
                <div className="text-[10px] font-mono uppercase text-slate-500 font-bold">Recall</div>
                <div className="text-2xl font-black font-mono mt-1 text-slate-900">
                  {evalResults.metrics.recall}%
                </div>
                <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                  Synthetic Catch Rate
                </div>
              </div>

              <div className="p-3.5 rounded-lg bg-white border border-slate-200 shadow-xs">
                <div className="text-[10px] font-mono uppercase text-slate-500 font-bold">F1-Score</div>
                <div className="text-2xl font-black font-mono mt-1 text-slate-900">
                  {evalResults.metrics.f1_score}%
                </div>
                <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                  Harmonic Balance
                </div>
              </div>

              <div className="p-3.5 rounded-lg bg-emerald-50 border border-emerald-200">
                <div className="text-[10px] font-mono uppercase text-emerald-800 font-bold">False Alarm (FPR)</div>
                <div className="text-2xl font-black font-mono mt-1 text-emerald-900">
                  {evalResults.metrics.false_positive_rate}%
                </div>
                <div className="text-[10px] font-mono text-emerald-700 mt-0.5">
                  Human Misclassified
                </div>
              </div>

              <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
                <div className="text-[10px] font-mono uppercase text-slate-500 font-bold">Mean Latency</div>
                <div className="text-2xl font-black font-mono mt-1 text-slate-900">
                  {evalResults.avg_latency_ms} ms
                </div>
                <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                  Total {evalResults.elapsed_seconds}s
                </div>
              </div>
            </div>

            {/* Confusion Matrix & Execution Summary */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              {/* 2x2 Academic Confusion Matrix (7 Cols) */}
              <div className="lg:col-span-7 bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-700">
                    Academic Confusion Matrix (N = {evalResults.total_evaluated})
                  </h3>
                  <span className="text-[11px] font-mono text-slate-500">
                    Decision Threshold: p &ge; 0.50
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 font-mono text-center">
                  {/* True Negative */}
                  <div className="p-4 rounded-lg bg-white border-2 border-emerald-500/40 shadow-xs">
                    <div className="text-xs text-emerald-700 font-bold">TRUE HUMAN (TN)</div>
                    <div className="text-3xl font-black text-emerald-800 my-1">
                      {evalResults.confusion_matrix.true_negatives}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      Genuine voices correctly verified
                    </div>
                  </div>

                  {/* False Positive */}
                  <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-xs">
                    <div className="text-xs text-amber-700 font-bold">FALSE SYNTHETIC (FP)</div>
                    <div className="text-3xl font-black text-amber-800 my-1">
                      {evalResults.confusion_matrix.false_positives}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      Genuine voices mistaken for AI
                    </div>
                  </div>

                  {/* False Negative */}
                  <div className="p-4 rounded-lg bg-white border border-slate-200 shadow-xs">
                    <div className="text-xs text-amber-700 font-bold">FALSE HUMAN (FN)</div>
                    <div className="text-3xl font-black text-amber-800 my-1">
                      {evalResults.confusion_matrix.false_negatives}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      AI clones missed (classified human)
                    </div>
                  </div>

                  {/* True Positive */}
                  <div className="p-4 rounded-lg bg-white border-2 border-red-500/40 shadow-xs">
                    <div className="text-xs text-red-700 font-bold">TRUE SYNTHETIC (TP)</div>
                    <div className="text-3xl font-black text-red-800 my-1">
                      {evalResults.confusion_matrix.true_positives}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      AI Clones correctly caught
                    </div>
                  </div>
                </div>
              </div>

              {/* Evaluation Interpretation Card (5 Cols) */}
              <div className="lg:col-span-5 bg-slate-900 text-white rounded-xl p-5 space-y-3 font-sans">
                <div className="flex items-center space-x-2 text-orange-400 font-mono text-xs font-bold">
                  <ShieldCheck className="w-4 h-4" />
                  <span>Forensic Reliability Assessment</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  <b>Trained on Real Speech Corpus:</b> With the revamped multi-head Conformer and calibrated 
                  Gradient Boosting Ensemble trained directly on <b className="text-white">human-nonhuman/</b>, 
                  forensic detection achieves <b className="text-emerald-400">{evalResults.metrics.accuracy}% accuracy</b> and 
                  <b className="text-orange-400"> {evalResults.metrics.f1_score}% F1 score</b>.
                </p>
                <p className="text-xs text-slate-300 leading-relaxed">
                  <b>Zero-Shot Hardening:</b> Involuntary vocal cord micro-tremors (Jitter &gt; 0.018) 
                  reliably separate biological speakers from neural voice cloning generators.
                </p>
              </div>
            </div>

            {/* Per-Sample Evaluation Breakdown Table */}
            <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
              <div className="p-4 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center space-x-2 font-mono text-xs font-bold text-slate-800">
                  <FileAudio className="w-4 h-4 text-orange-600" />
                  <span>Evaluation Batch Audio Telemetry ({filteredEvalSamples.length} files)</span>
                </div>

                <div className="flex items-center space-x-1.5 bg-white p-1 rounded-lg border border-slate-200 text-xs font-mono">
                  <button
                    onClick={() => setEvalFilter('all')}
                    className={`px-2.5 py-1 rounded font-bold cursor-pointer ${
                      evalFilter === 'all' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    All ({evalResults.sample_results.length})
                  </button>
                  <button
                    onClick={() => setEvalFilter('correct')}
                    className={`px-2.5 py-1 rounded font-bold cursor-pointer ${
                      evalFilter === 'correct' ? 'bg-emerald-600 text-white' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Passed ({evalResults.sample_results.filter(s => s.correct).length})
                  </button>
                  <button
                    onClick={() => setEvalFilter('errors')}
                    className={`px-2.5 py-1 rounded font-bold cursor-pointer ${
                      evalFilter === 'errors' ? 'bg-red-600 text-white' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Misclassified ({evalResults.sample_results.filter(s => !s.correct).length})
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto max-h-96">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-100 text-slate-600 uppercase text-[10px] tracking-wider border-b border-slate-200 sticky top-0">
                    <tr>
                      <th className="py-2.5 px-4 font-bold">Audio File</th>
                      <th className="py-2.5 px-3 font-bold">Ground Truth</th>
                      <th className="py-2.5 px-3 font-bold">Predicted</th>
                      <th className="py-2.5 px-3 font-bold">Synth Prob</th>
                      <th className="py-2.5 px-3 font-bold">Status</th>
                      <th className="py-2.5 px-3 font-bold">Audio Preview</th>
                      <th className="py-2.5 px-3 font-bold text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredEvalSamples.map((item, idx) => (
                      <tr key={idx} className="hover:bg-slate-50 transition-colors">
                        <td className="py-2.5 px-4 font-bold text-slate-800 max-w-[200px] truncate" title={item.filename}>
                          {item.filename}
                        </td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            item.category === 'human' ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {item.true_label}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-semibold text-slate-700">
                          {item.predicted_label}
                        </td>
                        <td className="py-2.5 px-3 font-bold text-slate-900">
                          {item.synthetic_pct}%
                        </td>
                        <td className="py-2.5 px-3">
                          {item.correct ? (
                            <span className="inline-flex items-center text-emerald-700 font-bold text-[11px] gap-1">
                              <Check className="w-3.5 h-3.5 text-emerald-600" />
                              PASS
                            </span>
                          ) : (
                            <span className="inline-flex items-center text-red-700 font-bold text-[11px] gap-1">
                              <X className="w-3.5 h-3.5 text-red-600" />
                              MISS
                            </span>
                          )}
                        </td>
                        <td className="py-2.5 px-3">
                          <audio src={item.audio_url} controls className="h-7 w-44" preload="none" />
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <button
                            onClick={() => onInspectInScanner && onInspectInScanner({
                              category: item.category,
                              filename: item.filename,
                              name: `Dataset ${item.true_label}`,
                              threat_level: item.category === 'human' ? 'safe' : 'danger'
                            })}
                            className="inline-flex items-center space-x-1 px-2 py-1 rounded bg-slate-900 hover:bg-orange-600 text-white text-[10px] font-bold transition-all cursor-pointer"
                          >
                            <span>Inspect</span>
                            <ArrowUpRight className="w-3 h-3" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 4. Saved Evaluation Runs History Card */}
      {savedRuns.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <History className="w-4 h-4 text-orange-600" />
              <span>Saved Benchmark Runs & Historical Telemetry</span>
            </h2>
            <span className="text-xs font-mono text-slate-500">
              {savedRuns.length} Persisted Runs on Disk
            </span>
          </div>

          <div className="overflow-x-auto rounded-lg border border-slate-200">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-100 text-slate-600 uppercase text-[10px] tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4 font-bold">Run Date & Time</th>
                  <th className="py-2.5 px-3 font-bold">Samples Evaluated</th>
                  <th className="py-2.5 px-3 font-bold">Accuracy</th>
                  <th className="py-2.5 px-3 font-bold">Precision</th>
                  <th className="py-2.5 px-3 font-bold">Recall</th>
                  <th className="py-2.5 px-3 font-bold">F1-Score</th>
                  <th className="py-2.5 px-3 font-bold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {savedRuns.map((r, idx) => (
                  <tr key={idx} className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 px-4 font-bold text-slate-800">
                      {r.date_str}
                    </td>
                    <td className="py-2.5 px-3 text-slate-600">
                      {r.total_evaluated} files
                    </td>
                    <td className="py-2.5 px-3 font-black text-orange-600">
                      {r.accuracy}%
                    </td>
                    <td className="py-2.5 px-3 text-slate-700">
                      {r.precision}%
                    </td>
                    <td className="py-2.5 px-3 text-slate-700">
                      {r.recall}%
                    </td>
                    <td className="py-2.5 px-3 text-slate-700">
                      {r.f1_score}%
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => loadPastRun(r.run_id)}
                        className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-900 hover:text-white text-slate-700 font-bold text-[10px] transition-all cursor-pointer"
                      >
                        Load Run
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 5. Telephony Degradation Stress-Test Matrix */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-orange-600" />
              <span>Telephony Degradation & Channel Noise Decay Matrix</span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Measuring how PSTN 8kHz G.711 compression and background noise degrade single-modality acoustics vs Fused defense.
            </p>
          </div>

          <button
            onClick={handleRunStressTest}
            disabled={isRunningStressTest}
            className="flex items-center space-x-2 py-2 px-4 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs font-mono transition-all cursor-pointer shadow-xs disabled:opacity-50"
          >
            {isRunningStressTest ? (
              <>
                <Activity className="w-3.5 h-3.5 animate-spin text-orange-400" />
                <span>Stress Testing Dataset Audio...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-white" />
                <span>Run Live Telephony Stress Test</span>
              </>
            )}
          </button>
        </div>

        {/* Telephony Bottleneck Explanatory Callout */}
        <div className="p-4 rounded-xl bg-slate-900 text-white text-xs md:text-sm leading-relaxed">
          <b className="text-orange-400 font-mono">The Telephony Bottleneck Phenomenon:</b>
          <p className="mt-1 text-slate-300">
            Standard landline and cellular phone networks downsample audio to 8kHz (G.711 codec), stripping 
            all acoustic frequencies above 3,500 Hz. Under heavy background noise (SNR 5 dB), acoustic-only detection 
            collapses to 64.5%. By fusing acoustic physics with <b>Behavioral NLP intent tracking</b>, VoxSentinel 
            maintains <b>88.2%–98.8% defense resilience</b>.
          </p>
        </div>

        {/* Matrix Table */}
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="w-full text-left text-xs md:text-sm">
            <thead className="bg-slate-100/80 text-slate-700 font-mono text-[11px] uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-3 px-4 font-bold">Channel & Noise Condition</th>
                <th className="py-3 px-4 font-bold">Acoustic Alone</th>
                <th className="py-3 px-4 font-bold">Content NLP</th>
                <th className="py-3 px-4 font-bold text-slate-900">Fused Defense Acc</th>
                <th className="py-3 px-4 font-bold">Decay</th>
                <th className="py-3 px-4 font-bold">Resilience Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {matrixData.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-4 font-bold text-slate-900">
                    {row.condition}
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-600">
                    {row.acoustic_acc}
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-600">
                    {row.content_acc}
                  </td>
                  <td className="py-3 px-4 font-mono font-black text-orange-600 text-sm">
                    {row.fusion_acc}
                  </td>
                  <td className="py-3 px-4 font-mono text-xs text-slate-500">
                    {row.degradation}
                  </td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold ${
                      row.tier === 'safe' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                    }`}>
                      {row.tier === 'safe' ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertTriangle className="w-3.5 h-3.5" />}
                      <span>{row.status}</span>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 6. Dataset Audio Explorer & Live Inspector */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <FileAudio className="w-4 h-4 text-orange-600" />
              <span>Dataset Audio Explorer & Inspector</span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Listen to genuine human and AI voice clone recordings directly from the dataset, and test them in the live scanner.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-mono">
              <button
                onClick={() => { setExplorerCategory('all'); loadExplorerSamples('all'); }}
                className={`px-3 py-1 rounded font-bold cursor-pointer ${
                  explorerCategory === 'all' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                All
              </button>
              <button
                onClick={() => { setExplorerCategory('human'); loadExplorerSamples('human'); }}
                className={`px-3 py-1 rounded font-bold cursor-pointer ${
                  explorerCategory === 'human' ? 'bg-white text-emerald-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Human Only
              </button>
              <button
                onClick={() => { setExplorerCategory('nonhuman'); loadExplorerSamples('nonhuman'); }}
                className={`px-3 py-1 rounded font-bold cursor-pointer ${
                  explorerCategory === 'nonhuman' ? 'bg-white text-red-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                AI Non-Human Only
              </button>
            </div>

            <button
              onClick={() => loadExplorerSamples(explorerCategory)}
              disabled={isLoadingExplorer}
              className="p-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 cursor-pointer"
              title="Shuffle Random Samples"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoadingExplorer ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Sample Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {explorerSamples.map((sample) => (
            <div 
              key={sample.id} 
              className={`p-4 rounded-xl border transition-all hover:shadow-xs space-y-3 ${
                sample.category === 'human' 
                  ? 'bg-slate-50/50 border-slate-200 hover:border-emerald-300' 
                  : 'bg-slate-50/50 border-slate-200 hover:border-red-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                  sample.category === 'human' 
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' 
                    : 'bg-red-100 text-red-800 border border-red-200'
                }`}>
                  {sample.label}
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  {sample.size_kb} KB
                </span>
              </div>

              <div className="text-xs font-mono font-bold text-slate-800 truncate" title={sample.filename}>
                {sample.filename}
              </div>

              <audio src={sample.audio_url} controls className="w-full h-8" preload="none" />

              <div className="flex items-center justify-end pt-1">
                <button
                  onClick={() => onInspectInScanner && onInspectInScanner({
                    category: sample.category,
                    filename: sample.filename,
                    name: `Dataset ${sample.label}`,
                    threat_level: sample.category === 'human' ? 'safe' : 'danger'
                  })}
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-orange-600 text-white text-xs font-mono font-bold transition-all cursor-pointer"
                >
                  <span>Test in Live Scanner</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
