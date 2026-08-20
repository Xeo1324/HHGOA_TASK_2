import React, { useState, useEffect } from 'react';
import { X, Send, Sparkles } from 'lucide-react';

interface TextQueryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (query: string) => void;
}

export const TextQueryModal: React.FC<TextQueryModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [query, setQuery] = useState('');

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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    onSubmit(query.trim());
    setQuery('');
    onClose();
  };

  const sampleSuggestions = [
    'What is a corporation?',
    'What is photosynthesis?',
    'प्रकाश संश्लेषण क्या है?',
    'What is Python programming language?',
  ];

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="text-query-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-fade-in"
    >
      <div className="w-full max-w-lg bg-[#FBF9F4] text-[#111111] rounded-lg p-6 sm:p-8 border border-[#D8D2C7] shadow-xl relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          aria-label="Close"
          className="absolute top-5 right-5 p-1.5 rounded-md hover:bg-[#EEE9DF] text-[#4A4741] hover:text-[#111111] transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Headline */}
        <h3 id="text-query-title" className="text-lg font-semibold tracking-wide uppercase text-[#111111] mb-1">
          Type Your Inquiry
        </h3>
        <p className="text-xs text-[#4A4741] mb-5">
          Query the MSMARCO-XI grounded RAG pipeline directly
        </p>

        {/* Input Form */}
        <form onSubmit={handleSubmit}>
          <div className="relative mb-4">
            <textarea
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your question (e.g. What is a corporation?)..."
              rows={3}
              className="w-full bg-[#F7F3EA] border border-[#D8D2C7] focus:border-[#111111] rounded-md p-3.5 text-sm text-[#111111] placeholder-[#4A4741]/50 focus:outline-none transition-colors font-editorial resize-none"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />
          </div>

          {/* Sample Prompts */}
          <div className="mb-6">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-[#4A4741] block mb-2">
              Verified Suggestions
            </span>
            <div className="flex flex-wrap gap-1.5">
              {sampleSuggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setQuery(suggestion)}
                  className="text-left text-xs px-2.5 py-1 rounded bg-[#F7F3EA] hover:bg-[#EEE9DF] border border-[#D8D2C7] text-[#111111] transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-2 rounded-md text-xs font-medium text-[#4A4741] hover:text-[#111111] hover:bg-[#EEE9DF] transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!query.trim()}
              className="flex items-center gap-1.5 px-5 py-2 rounded-md bg-[#111111] hover:bg-[#222222] text-[#F7F3EA] text-xs font-semibold transition-all disabled:opacity-30 shadow-xs"
            >
              <span>Submit Query</span>
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TextQueryModal;
