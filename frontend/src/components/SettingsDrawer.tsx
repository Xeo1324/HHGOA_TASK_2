import React, { useEffect } from 'react';
import { X, Sliders, Volume2, Globe, Database, Cpu, Server } from 'lucide-react';
import { Settings } from '../types';

interface SettingsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  settings: Settings;
  onUpdateSettings: (newSettings: Partial<Settings>) => void;
}

export const SettingsDrawer: React.FC<SettingsDrawerProps> = ({
  isOpen,
  onClose,
  settings,
  onUpdateSettings,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="settings-drawer-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
      className="fixed inset-0 z-40 flex justify-end bg-black/40 backdrop-blur-xs lg:left-64 transition-opacity animate-fade-in"
    >
      <div className="w-full max-w-md bg-[#FBF9F4] text-[#111111] h-full p-6 sm:p-8 overflow-y-auto border-l border-[#D8D2C7] shadow-xl flex flex-col justify-between">
        <div>
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-[#D8D2C7] mb-6">
            <div className="flex items-center gap-2.5">
              <Sliders className="w-5 h-5 text-[#111111]" />
              <div>
                <h2 id="settings-drawer-title" className="text-base font-semibold uppercase tracking-wider text-[#111111]">
                  System Configuration
                </h2>
                <p className="text-[11px] text-[#4A4741]">
                  RAG Pipeline & Audio Parameters
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              aria-label="Close Settings"
              className="p-1.5 rounded-md hover:bg-[#EEE9DF] text-[#4A4741] hover:text-[#111111] transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="space-y-6">
            {/* Language */}
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-[#4A4741] flex items-center gap-1.5 mb-2">
                <Globe className="w-3.5 h-3.5" />
                <span>Primary Language</span>
              </label>
              <select
                value={settings.language}
                onChange={(e) => onUpdateSettings({ language: e.target.value })}
                className="w-full bg-[#F7F3EA] border border-[#D8D2C7] focus:border-[#111111] rounded-md p-2.5 text-xs text-[#111111] focus:outline-none"
              >
                <option value="en">English (EN)</option>
                <option value="hi">Hindi (HI - हिन्दी)</option>
                <option value="te">Telugu (TE - తెలుగు)</option>
                <option value="ta">Tamil (TA - தமிழ்)</option>
                <option value="bn">Bengali (BN - বাংলা)</option>
                <option value="mr">Marathi (MR - मराठी)</option>
                <option value="gu">Gujarati (GU - ગુજરાતી)</option>
                <option value="kn">Kannada (KN - ಕನ್ನಡ)</option>
                <option value="ml">Malayalam (ML - മലയാളം)</option>
                <option value="pa">Punjabi (PA - ਪੰਜਾਬੀ)</option>
                <option value="ur">Urdu (UR - اردو)</option>
              </select>
            </div>

            {/* Retrieval Strategy */}
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-[#4A4741] flex items-center gap-1.5 mb-2">
                <Cpu className="w-3.5 h-3.5" />
                <span>Retrieval Strategy</span>
              </label>
              <select
                value={settings.retrieval_mode}
                onChange={(e) => onUpdateSettings({ retrieval_mode: e.target.value as any })}
                className="w-full bg-[#F7F3EA] border border-[#D8D2C7] focus:border-[#111111] rounded-md p-2.5 text-xs text-[#111111] focus:outline-none"
              >
                <option value="hybrid_rerank">Hybrid RRF + FlashRank Reranker (Recommended)</option>
                <option value="hybrid">Hybrid RRF (Dense + BM25 Fusion)</option>
                <option value="dense">Dense Vector Search (Vectorized NumPy BLAS)</option>
                <option value="bm25">BM25 Lexical Inverted Search</option>
              </select>
            </div>

            {/* Chunking Strategy */}
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-[#4A4741] flex items-center gap-1.5 mb-2">
                <Database className="w-3.5 h-3.5" />
                <span>Chunking Granularity</span>
              </label>
              <select
                value={settings.chunking_strategy}
                onChange={(e) => onUpdateSettings({ chunking_strategy: e.target.value as any })}
                className="w-full bg-[#F7F3EA] border border-[#D8D2C7] focus:border-[#111111] rounded-md p-2.5 text-xs text-[#111111] focus:outline-none"
              >
                <option value="sentence">Sentence Window Boundary</option>
                <option value="fixed">Fixed-Size Sliding Windows (256 Tokens)</option>
                <option value="hierarchical">Hierarchical Document Structure</option>
              </select>
            </div>

            {/* Top-K Evidence Limit */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-xs font-semibold uppercase tracking-wider text-[#4A4741]">
                  Top-K Evidence Passages
                </label>
                <span className="font-mono text-xs font-bold text-[#111111]">{settings.top_k}</span>
              </div>
              <input
                type="range"
                min="1"
                max="10"
                value={settings.top_k}
                onChange={(e) => onUpdateSettings({ top_k: parseInt(e.target.value, 10) })}
                className="w-full accent-[#111111] bg-[#EEE9DF] h-1.5 rounded"
              />
            </div>

            {/* Audio Synthesis Toggle */}
            <div className="flex items-center justify-between p-3.5 rounded-md bg-[#F7F3EA] border border-[#D8D2C7]">
              <div className="flex items-center gap-2">
                <Volume2 className="w-4 h-4 text-[#111111]" />
                <div>
                  <div className="text-xs font-semibold text-[#111111]">Voice Playback (TTS)</div>
                  <div className="text-[10px] text-[#4A4741]">Synthesize spoken answers via Edge TTS</div>
                </div>
              </div>
              <input
                type="checkbox"
                checked={settings.synthesize_audio}
                onChange={(e) => onUpdateSettings({ synthesize_audio: e.target.checked })}
                className="w-4 h-4 accent-[#111111] rounded"
              />
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-6 border-t border-[#D8D2C7] text-[11px] text-[#4A4741] flex items-center justify-between">
          <span>NOVARON v0.5.0</span>
          <span>Task 2 · HH Goa</span>
        </div>
      </div>
    </div>
  );
};

export default SettingsDrawer;
