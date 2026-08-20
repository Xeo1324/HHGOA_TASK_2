import React, { useState } from 'react';
import { Volume2, Pause, Copy, Check, Share2, Database, Zap, ChevronDown, ChevronUp, CheckCircle2 } from 'lucide-react';
import { QueryResponse, VoiceQueryResponse } from '../types';

interface AnswerCardProps {
  data: QueryResponse | VoiceQueryResponse;
  isPlaying: boolean;
  onToggleAudio: () => void;
  onShare?: () => void;
  onSelectSuggestion?: (question: string) => void;
}

export const AnswerCard: React.FC<AnswerCardProps> = ({
  data,
  isPlaying,
  onToggleAudio,
  onShare,
  onSelectSuggestion,
}) => {
  const [sourcesExpanded, setSourcesExpanded] = useState(false);
  const [latencyExpanded, setLatencyExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const queryText = 'query' in data ? data.query : undefined;
  const normalizedQuery = data.normalized_query;
  const sources = data.sources || [];
  const latency = data.latency_ms || {};
  const suggestedQuestions = data.suggested_questions || [];

  const handleCopy = () => {
    navigator.clipboard.writeText(data.answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const totalLatencyFormatted = latency.total
    ? `${Math.round(latency.total)}ms`
    : `${Math.round(latency.rag_total || 0)}ms`;

  const renderInlineCitations = (content: string) => {
    const parts = content.split(/(\[\d+\])/g);
    return parts.map((part, index) => {
      const match = part.match(/^\[(\d+)\]$/);
      if (match) {
        return (
          <span
            key={index}
            className="inline-flex items-center justify-center font-mono text-[11px] font-semibold text-[#111111] bg-[#EEE9DF] border border-[#D8D2C7] rounded px-1.5 py-0.2 mx-0.5 align-baseline"
          >
            {match[1]}
          </span>
        );
      }
      return part;
    });
  };

  const renderParagraph = (block: string, pIdx: number) => {
    const lines = block.split('\n').map((l) => l.trim()).filter(Boolean);
    const isListBlock = lines.some((l) => l.startsWith('- ') || l.startsWith('* ') || l.startsWith('• ') || /^\d+\.\s+/.test(l));

    if (isListBlock) {
      return (
        <ul key={pIdx} className="space-y-1.5 my-2">
          {lines.map((line, lIdx) => {
            const numberedMatch = line.match(/^(\d+)\.\s+(.*)/);
            if (numberedMatch) {
              return (
                <li key={lIdx} className="flex items-start gap-2 ml-1">
                  <span className="font-mono text-xs font-semibold text-[#4A4741] mt-0.5 shrink-0">
                    {numberedMatch[1]}.
                  </span>
                  <span className="leading-relaxed">{renderInlineCitations(numberedMatch[2])}</span>
                </li>
              );
            }

            const bulletMatch = line.match(/^[-*•]\s+(.*)/);
            if (bulletMatch) {
              return (
                <li key={lIdx} className="flex items-start gap-2 ml-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#111111] mt-2 shrink-0" />
                  <span className="leading-relaxed">{renderInlineCitations(bulletMatch[1])}</span>
                </li>
              );
            }

            return (
              <li key={lIdx} className="leading-relaxed">
                {renderInlineCitations(line)}
              </li>
            );
          })}
        </ul>
      );
    }

    return (
      <p key={pIdx} className="leading-relaxed text-[#111111] font-editorial text-[17px]">
        {renderInlineCitations(block)}
      </p>
    );
  };

  return (
    <article className="w-full max-w-3xl bg-[#FBF9F4] rounded-lg border border-[#D8D2C7] shadow-xs overflow-hidden transition-all animate-fade-in my-6">
      {/* Header Bar */}
      <div className="flex items-center justify-between px-6 py-3.5 border-b border-[#D8D2C7] bg-[#F7F3EA]/70">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-semibold tracking-wider uppercase bg-[#EEE9DF] text-[#111111] border border-[#D8D2C7]">
            <CheckCircle2 className="w-3 h-3 text-emerald-700" />
            Grounded Answer
          </span>
          <span className="text-xs text-[#4A4741] hidden sm:inline-block">
            {sources.length} cited source{sources.length === 1 ? '' : 's'}
          </span>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={onToggleAudio}
            className={`px-2.5 py-1 rounded text-xs font-medium border transition-colors flex items-center gap-1.5 ${
              isPlaying
                ? 'bg-[#111111] text-[#F7F3EA] border-[#111111]'
                : 'bg-[#FBF9F4] text-[#111111] border-[#D8D2C7] hover:bg-[#EEE9DF]'
            }`}
            title={isPlaying ? 'Pause audio reading' : 'Read answer aloud'}
          >
            {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
            <span>{isPlaying ? 'Pause' : 'Listen'}</span>
          </button>

          <button
            onClick={handleCopy}
            className="p-1.5 rounded text-[#4A4741] hover:text-[#111111] hover:bg-[#EEE9DF] border border-[#D8D2C7] transition-colors"
            title="Copy answer text"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-700" /> : <Copy className="w-3.5 h-3.5" />}
          </button>

          {onShare && (
            <button
              onClick={onShare}
              className="p-1.5 rounded text-[#4A4741] hover:text-[#111111] hover:bg-[#EEE9DF] border border-[#D8D2C7] transition-colors"
              title="Share citation"
            >
              <Share2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="p-6 sm:p-8 space-y-6">
        {/* Question Block */}
        <div>
          <div className="text-[11px] font-semibold tracking-[0.16em] uppercase text-[#4A4741] mb-1.5">
            Question
          </div>
          <h2 className="font-editorial text-2xl sm:text-3xl text-[#111111] font-normal leading-snug">
            {queryText || normalizedQuery}
          </h2>
          {normalizedQuery && queryText && normalizedQuery !== queryText && (
            <p className="text-xs text-[#4A4741] font-mono mt-1">
              Normalized: {normalizedQuery}
            </p>
          )}
        </div>

        {/* Answer Block */}
        <div>
          <div className="text-[11px] font-semibold tracking-[0.16em] uppercase text-[#4A4741] mb-2">
            Synthesized Answer
          </div>
          <div className="space-y-3 font-editorial text-lg text-[#111111] leading-relaxed">
            {data.answer.split('\n\n').map((para, idx) => renderParagraph(para, idx))}
          </div>
        </div>

        {/* Sources Section */}
        {sources.length > 0 && (
          <div className="pt-4 border-t border-[#D8D2C7]">
            <div className="flex items-center justify-between mb-3">
              <div className="text-[11px] font-semibold tracking-[0.16em] uppercase text-[#4A4741] flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-[#111111]" />
                Sources & Provenance ({sources.length})
              </div>
              <button
                onClick={() => setSourcesExpanded(!sourcesExpanded)}
                className="text-xs text-[#4A4741] hover:text-[#111111] flex items-center gap-1 font-medium"
              >
                {sourcesExpanded ? 'Collapse' : 'Expand All'}
                {sourcesExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>
            </div>

            <div className="space-y-2">
              {(sourcesExpanded ? sources : sources.slice(0, 2)).map((source, index) => (
                <div
                  key={source.chunk_id || index}
                  className="p-3.5 rounded-md bg-[#F7F3EA] border border-[#D8D2C7] hover:border-[#111111] transition-colors"
                >
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-[#111111] bg-[#EEE9DF] px-1.5 py-0.5 rounded border border-[#D8D2C7]">
                        [{index + 1}]
                      </span>
                      <span className="text-xs font-semibold text-[#111111] truncate max-w-[240px] sm:max-w-md">
                        {source.title || source.document_id}
                      </span>
                    </div>
                    <span className="text-[11px] font-mono text-[#4A4741] shrink-0">
                      Score: {source.relevance_score ? source.relevance_score.toFixed(3) : '0.000'}
                    </span>
                  </div>

                  <p className="text-xs text-[#4A4741] font-editorial line-clamp-2 leading-relaxed mt-1">
                    "{source.text}"
                  </p>

                  <div className="flex items-center gap-2 mt-2 pt-1.5 border-t border-[#D8D2C7]/60 text-[10px] font-mono text-[#4A4741]">
                    <span>ID: {source.chunk_id || source.passage_id || source.document_id}</span>
                    <span>•</span>
                    <span className="uppercase">{source.language || 'en'}</span>
                    <span>•</span>
                    <span>MSMARCO-XI</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Latency & Telemetry Details */}
        <div className="pt-3 border-t border-[#D8D2C7] flex flex-wrap items-center justify-between text-xs text-[#4A4741]">
          <button
            onClick={() => setLatencyExpanded(!latencyExpanded)}
            className="flex items-center gap-1.5 hover:text-[#111111] transition-colors font-mono text-[11px]"
          >
            <Zap className="w-3.5 h-3.5 text-emerald-800" />
            <span>Total Latency: {totalLatencyFormatted}</span>
            {latencyExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>

          <span className="text-[11px] font-mono">
            Mode: {data.retrieval_strategy || 'Hybrid RAG'}
          </span>
        </div>

        {latencyExpanded && (
          <div className="p-3 bg-[#EEE9DF] rounded-md border border-[#D8D2C7] text-xs font-mono space-y-1">
            <div className="flex justify-between">
              <span>Query Normalization:</span>
              <span>{latency.norm ? `${Math.round(latency.norm)}ms` : '0ms'}</span>
            </div>
            <div className="flex justify-between">
              <span>Local Retrieval (Dense + BM25 + RRF):</span>
              <span>{latency.retrieval ? `${Math.round(latency.retrieval)}ms` : `${Math.round(latency.rag_total || 0)}ms`}</span>
            </div>
            {latency.rerank !== undefined && (
              <div className="flex justify-between">
                <span>Reranking:</span>
                <span>{Math.round(latency.rerank)}ms</span>
              </div>
            )}
            {latency.generation !== undefined && (
              <div className="flex justify-between">
                <span>Grounded LLM Generation:</span>
                <span>{Math.round(latency.generation)}ms</span>
              </div>
            )}
            {latency.tts !== undefined && (
              <div className="flex justify-between">
                <span>Speech Synthesis (TTS):</span>
                <span>{Math.round(latency.tts)}ms</span>
              </div>
            )}
          </div>
        )}

        {/* Suggested Questions */}
        {suggestedQuestions.length > 0 && onSelectSuggestion && (
          <div className="pt-2">
            <div className="text-[11px] font-semibold tracking-[0.16em] uppercase text-[#4A4741] mb-2">
              Related Inquiries
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
      </div>
    </article>
  );
};

export default AnswerCard;
