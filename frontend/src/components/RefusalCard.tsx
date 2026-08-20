import React, { useState } from 'react';
import { ShieldAlert, Volume2, Pause, RotateCcw, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';
import { QueryResponse, VoiceQueryResponse } from '../types';

interface RefusalCardProps {
  data: QueryResponse | VoiceQueryResponse;
  isPlaying: boolean;
  onToggleAudio: () => void;
  onReset: () => void;
  onSelectSuggestion?: (question: string) => void;
}

export const RefusalCard: React.FC<RefusalCardProps> = ({
  data,
  isPlaying,
  onToggleAudio,
  onReset,
  onSelectSuggestion,
}) => {
  const [showExplanation, setShowExplanation] = useState(false);
  const queryText = 'query' in data ? data.query : undefined;
  const normalizedQuery = data.normalized_query;
  const suggestedQuestions = (data.suggested_questions && data.suggested_questions.length > 0)
    ? data.suggested_questions
    : [
        'What is a corporation?',
        'What is photosynthesis?',
        'What is Python programming language?',
      ];

  return (
    <article className="w-full max-w-3xl bg-[#FBF9F4] rounded-lg border border-[#D8D2C7] shadow-xs overflow-hidden transition-all animate-fade-in my-6">
      {/* Header Bar */}
      <div className="flex items-center justify-between px-6 py-3.5 border-b border-[#D8D2C7] bg-[#F7F3EA]/70">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-semibold tracking-wider uppercase bg-[#EEE9DF] text-[#111111] border border-[#D8D2C7]">
            <ShieldAlert className="w-3 h-3 text-amber-700" />
            Grounded Refusal Guardrail
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={onToggleAudio}
            className={`px-2.5 py-1 rounded text-xs font-medium border transition-colors flex items-center gap-1.5 ${
              isPlaying
                ? 'bg-[#111111] text-[#F7F3EA] border-[#111111]'
                : 'bg-[#FBF9F4] text-[#111111] border-[#D8D2C7] hover:bg-[#EEE9DF]'
            }`}
          >
            {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
            <span>{isPlaying ? 'Pause' : 'Listen'}</span>
          </button>

          <button
            onClick={onReset}
            className="p-1.5 rounded text-[#4A4741] hover:text-[#111111] hover:bg-[#EEE9DF] border border-[#D8D2C7] transition-colors"
            title="Ask another question"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="p-6 sm:p-8 space-y-5">
        {/* Question */}
        <div>
          <div className="text-[11px] font-semibold tracking-[0.16em] uppercase text-[#4A4741] mb-1">
            Question
          </div>
          <h2 className="font-editorial text-2xl text-[#111111] font-normal leading-snug">
            {queryText || normalizedQuery}
          </h2>
        </div>

        {/* Refusal Notice */}
        <div className="p-4 rounded-md bg-[#EEE9DF] border border-[#D8D2C7] text-sm text-[#111111] font-editorial space-y-2">
          <div className="flex items-center gap-2 font-sans font-semibold text-xs text-[#111111]">
            <AlertCircle className="w-4 h-4 text-amber-800 shrink-0" />
            <span>Insufficient Grounded Evidence</span>
          </div>
          <p className="leading-relaxed text-[16px]">
            {data.answer || "I don't have enough verified information in the indexed knowledge base to answer that reliably."}
          </p>
        </div>

        {/* Suggested Alternatives */}
        {suggestedQuestions.length > 0 && onSelectSuggestion && (
          <div>
            <div className="text-[11px] font-semibold tracking-[0.16em] uppercase text-[#4A4741] mb-2">
              Verified Inquiries Available in Corpus
            </div>
            <div className="flex flex-wrap gap-2">
              {suggestedQuestions.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => onSelectSuggestion(q)}
                  className="px-3 py-1.5 rounded-md bg-[#F7F3EA] hover:bg-[#EEE9DF] border border-[#D8D2C7] text-xs text-[#111111] transition-colors text-left"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Explanatory Collapsible */}
        <div className="pt-3 border-t border-[#D8D2C7]">
          <button
            onClick={() => setShowExplanation(!showExplanation)}
            className="w-full flex items-center justify-between text-xs text-[#4A4741] hover:text-[#111111] py-1"
          >
            <span>Policy: Why does NOVARON refuse?</span>
            {showExplanation ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showExplanation && (
            <p className="mt-2 text-xs text-[#4A4741] font-sans leading-relaxed p-3 bg-[#EEE9DF]/60 rounded border border-[#D8D2C7]">
              To guarantee zero hallucinations, NOVARON strictly requires retrieved candidate relevance scores to meet verified confidence thresholds. When a question is out-of-domain, unsupported, or ambiguous, refusal is enforced rather than speculative guessing.
            </p>
          )}
        </div>
      </div>
    </article>
  );
};

export default RefusalCard;
