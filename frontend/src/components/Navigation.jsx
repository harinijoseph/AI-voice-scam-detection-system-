import React from 'react';
import { ShieldAlert, Microscope, MessageSquareWarning } from 'lucide-react';

export default function Navigation({ activeTab, setActiveTab }) {
  const tabs = [
    {
      id: 'scanner',
      num: '01',
      title: 'Live Voice Scanner',
      subtitle: 'Detection Hub & Real-Time Verdict',
      icon: ShieldAlert
    },
    {
      id: 'physics',
      num: '02',
      title: 'Vocal Physics Lab',
      subtitle: 'Pitch & Vocoder Metrics',
      icon: Microscope
    },
    {
      id: 'conversation',
      num: '03',
      title: 'Scam Words & Funnel',
      subtitle: 'Coercive Tactics NLP',
      icon: MessageSquareWarning
    }
  ];

  return (
    <nav className="w-full bg-slate-900 border-b border-slate-800 text-white px-4 py-2 shadow-xs">
      <div className="max-w-7xl mx-auto flex items-center justify-between overflow-x-auto gap-2 scrollbar-none">
        <div className="flex items-center space-x-2 min-w-max">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2.5 px-4 py-2 rounded-lg text-left transition-all duration-150 cursor-pointer ${
                  isActive
                    ? 'bg-orange-600 text-white shadow-xs font-bold'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/80 font-medium'
                }`}
              >
                <div className={`p-1.5 rounded-md ${isActive ? 'bg-orange-700/60 text-white' : 'bg-slate-800 text-slate-400'}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center space-x-1.5">
                    <span className={`text-[10px] font-mono tracking-wider uppercase ${isActive ? 'text-orange-200' : 'text-slate-400'}`}>
                      {tab.num}
                    </span>
                    <span className="text-xs leading-none font-bold">
                      {tab.title}
                    </span>
                  </div>
                  <div className={`text-[11px] leading-tight mt-0.5 ${isActive ? 'text-orange-100' : 'text-slate-400'}`}>
                    {tab.subtitle}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
