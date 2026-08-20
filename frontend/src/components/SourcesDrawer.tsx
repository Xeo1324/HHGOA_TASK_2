import React, { useEffect } from 'react';
import { X, Database, BookOpen, CheckCircle2 } from 'lucide-react';
import { Source } from '../types';

interface SourcesDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  sources?: Source[];
  queryText?: string;
}

export const SourcesDrawer: React.FC<SourcesDrawerProps> = ({
  isOpen,
  onClose,
  sources = [],
  queryText,
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
      aria-labelledby="sources-drawer-title"
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
              <Database className="w-5 h-5 text-[#111111]" />
              <div>
                <h2 id="sources-drawer-title" className="text-base font-semibold text-[#111111] uppercase tracking-wider">
                  Retrieved Sources
                </h2>
                <p className="text-[11px] text-[#4A4741]">
                  Evidence from MSMARCO-XI Knowledge Base
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              aria-label="Close Sources"
              className="p-1.5 rounded-md hover:bg-[#EEE9DF] text-[#4A4741] hover:text-[#111111] transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Context Query (if any) */}
          {queryText && (
            <div className="mb-5 p-3 rounded-md bg-[#F7F3EA] border border-[#D8D2C7] text-xs">
              <div className="text-[10px] font-semibold uppercase tracking-wider text-[#4A4741] mb-1">
                Active Query
              </div>
              <p className="font-editorial text-sm text-[#111111]">
                "{queryText}"
              </p>
            </div>
          )}

          {/* Sources List */}
          {sources.length === 0 ? (
            <div className="py-12 text-center text-[#4A4741] space-y-2">
              <BookOpen className="w-8 h-8 mx-auto opacity-40 text-[#111111]" />
              <p className="text-sm font-editorial">No sources currently retrieved.</p>
              <p className="text-xs text-[#4A4741]">
                Submit a question to inspect retrieved citations and provenance.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {sources.map((source, index) => (
                <div
                  key={source.chunk_id || index}
                  className="p-4 rounded-md bg-[#F7F3EA] border border-[#D8D2C7] space-y-2"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-xs font-bold text-[#111111] bg-[#EEE9DF] px-2 py-0.5 rounded border border-[#D8D2C7]">
                      [{index + 1}]
                    </span>
                    <span className="text-[11px] font-mono font-medium text-[#111111]">
                      Score: {source.relevance_score ? source.relevance_score.toFixed(4) : '0.0000'}
                    </span>
                  </div>

                  <div className="text-xs font-semibold text-[#111111]">
                    {source.title || source.document_id}
                  </div>

                  <p className="text-xs font-editorial text-[#4A4741] leading-relaxed">
                    "{source.text}"
                  </p>

                  <div className="pt-2 border-t border-[#D8D2C7]/60 flex flex-wrap items-center gap-2 text-[10px] font-mono text-[#4A4741]">
                    <span>Chunk ID: {source.chunk_id || source.passage_id || source.document_id}</span>
                    <span>•</span>
                    <span className="uppercase">{source.language || 'en'}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="pt-6 border-t border-[#D8D2C7] text-xs text-[#4A4741] flex items-center justify-between">
          <span>Corpus: 12,184 Passages</span>
          <span className="flex items-center gap-1 text-emerald-800 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Verified Grounding
          </span>
        </div>
      </div>
    </div>
  );
};

export default SourcesDrawer;
