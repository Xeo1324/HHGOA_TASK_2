import React, { useEffect } from 'react';
import { X, History, ArrowRight, Trash2, CheckCircle2, ShieldAlert } from 'lucide-react';
import { QueryResponse, VoiceQueryResponse } from '../types';

interface HistoryItem {
  id: string;
  timestamp: Date;
  query: string;
  data: QueryResponse | VoiceQueryResponse;
}

interface HistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  history: HistoryItem[];
  onSelectHistory: (item: HistoryItem) => void;
  onClearHistory: () => void;
}

export const HistoryDrawer: React.FC<HistoryDrawerProps> = ({
  isOpen,
  onClose,
  history,
  onSelectHistory,
  onClearHistory,
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

  const formatTimestamp = (date: Date) => {
    try {
      const now = new Date();
      const isToday =
        date.getDate() === now.getDate() &&
        date.getMonth() === now.getMonth() &&
        date.getFullYear() === now.getFullYear();

      const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      return isToday ? `Today · ${timeStr}` : `${date.toLocaleDateString([], { month: 'short', day: 'numeric' })} · ${timeStr}`;
    } catch {
      return 'Recent';
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="history-drawer-title"
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
              <History className="w-5 h-5 text-[#111111]" />
              <div>
                <h2 id="history-drawer-title" className="text-base font-semibold uppercase tracking-wider text-[#111111]">
                  Query Session Log
                </h2>
                <p className="text-[11px] text-[#4A4741]">
                  {history.length} recorded quer{history.length === 1 ? 'y' : 'ies'}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              aria-label="Close History"
              className="p-1.5 rounded-md hover:bg-[#EEE9DF] text-[#4A4741] hover:text-[#111111] transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* History List */}
          {history.length === 0 ? (
            <div className="py-16 text-center text-[#4A4741] space-y-2">
              <History className="w-8 h-8 mx-auto opacity-30 text-[#111111]" />
              <p className="text-sm font-editorial">No inquiries in current session.</p>
              <p className="text-xs text-[#4A4741]">
                Voice queries and keyboard submissions will be logged here.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {history.map((item) => {
                const isRefused = item.data.refused;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      onSelectHistory(item);
                      onClose();
                    }}
                    className="w-full text-left p-3.5 rounded-md bg-[#F7F3EA] border border-[#D8D2C7] hover:border-[#111111] transition-all group"
                  >
                    <div className="flex items-center justify-between gap-2 mb-1.5">
                      <span className="text-[10px] font-mono text-[#4A4741]">
                        {formatTimestamp(item.timestamp)}
                      </span>
                      {isRefused ? (
                        <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-amber-800 bg-[#EEE9DF] px-2 py-0.5 rounded border border-[#D8D2C7]">
                          <ShieldAlert className="w-3 h-3" />
                          Refused
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-800 bg-[#EEE9DF] px-2 py-0.5 rounded border border-[#D8D2C7]">
                          <CheckCircle2 className="w-3 h-3" />
                          Grounded
                        </span>
                      )}
                    </div>

                    <p className="font-editorial text-sm font-medium text-[#111111] line-clamp-1 group-hover:underline">
                      "{item.query}"
                    </p>

                    <div className="flex items-center justify-between mt-2 pt-1.5 border-t border-[#D8D2C7]/60 text-[10px] font-mono text-[#4A4741]">
                      <span>
                        {item.data.sources?.length || 0} cited passage{item.data.sources?.length === 1 ? '' : 's'}
                      </span>
                      <span className="flex items-center gap-1 group-hover:text-[#111111]">
                        <span>View</span>
                        <ArrowRight className="w-3 h-3" />
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        {history.length > 0 && (
          <div className="pt-4 border-t border-[#D8D2C7] flex items-center justify-between">
            <button
              onClick={onClearHistory}
              className="flex items-center gap-1.5 text-xs text-[#4A4741] hover:text-red-700 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear Log</span>
            </button>
            <span className="text-[11px] font-mono text-[#4A4741]">
              Session Storage
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoryDrawer;
