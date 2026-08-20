import React, { useState, useEffect } from 'react';
import { X, Copy, Check, Share2 } from 'lucide-react';
import { QueryResponse, VoiceQueryResponse } from '../types';

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: QueryResponse | VoiceQueryResponse;
}

export const ShareModal: React.FC<ShareModalProps> = ({
  isOpen,
  onClose,
  data,
}) => {
  const [copied, setCopied] = useState(false);

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

  const queryText = 'query' in data ? data.query : 'Grounded Inquiry';
  const totalMs = data.latency_ms?.total || data.latency_ms?.rag_total || 0;
  const latencyStr = totalMs > 1000 ? `${(totalMs / 1000).toFixed(2)}s` : `${Math.round(totalMs)}ms`;

  const shareText = `NOVARON Grounded Voice RAG\n\nInquiry: "${queryText}"\nAnswer: "${data.answer.slice(0, 150)}..."\n\nVerified Latency: ${latencyStr} · ${data.sources?.length || 0} Grounded Sources (MSMARCO-XI)`;

  const handleCopyText = () => {
    navigator.clipboard.writeText(shareText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="share-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in"
    >
      <div className="w-full max-w-md bg-[#FBF9F4] text-[#111111] rounded-lg p-6 sm:p-8 border border-[#D8D2C7] shadow-xl relative">
        <button
          onClick={onClose}
          aria-label="Close"
          className="absolute top-5 right-5 p-1.5 rounded-md hover:bg-[#EEE9DF] text-[#4A4741] hover:text-[#111111] transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 mb-1">
          <Share2 className="w-4 h-4 text-[#111111]" />
          <h3 id="share-modal-title" className="text-base font-semibold uppercase tracking-wider text-[#111111]">
            Share Grounded Result
          </h3>
        </div>
        <p className="text-xs text-[#4A4741] mb-4">
          Export verified inquiry citations
        </p>

        {/* Preview Card */}
        <div className="p-3.5 rounded-md bg-[#F7F3EA] border border-[#D8D2C7] font-editorial text-xs text-[#111111] mb-5 whitespace-pre-wrap leading-relaxed">
          {shareText}
        </div>

        <div className="flex items-center justify-end gap-2.5">
          <button
            onClick={onClose}
            className="px-3.5 py-2 rounded-md text-xs font-medium text-[#4A4741] hover:text-[#111111] hover:bg-[#EEE9DF] transition-colors"
          >
            Close
          </button>
          <button
            onClick={handleCopyText}
            className="flex items-center justify-center gap-2 py-2 px-5 rounded-md bg-[#111111] hover:bg-[#222222] text-[#F7F3EA] text-xs font-semibold transition-all shadow-xs"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
            <span>{copied ? 'Copied' : 'Copy Citation'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ShareModal;
