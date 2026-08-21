import React from 'react';
import { Mic, Activity, Globe } from 'lucide-react';
import { AppState } from '../types';

interface LiveTranscriptionProps {
  state: AppState;
  finalTranscript: string;
  interimTranscript: string;
  language?: string;
  onClear?: () => void;
}

export const LiveTranscription: React.FC<LiveTranscriptionProps> = ({
  state,
  finalTranscript,
  interimTranscript,
  language = 'en',
}) => {
  const isListening = state === 'LISTENING';
  const isTranscribing = state === 'TRANSCRIBING';

  // Only render during active voice query or transcription
  if (!isListening && !isTranscribing) {
    return null;
  }

  const hasContent = Boolean(finalTranscript.trim() || interimTranscript.trim());

  return (
    <div
      role="region"
      aria-label="Live Speech Transcription"
      className="w-full max-w-xl mx-auto my-3 px-4 py-3 rounded-xl bg-[#FBF9F4]/95 border border-[#D8D2C7] shadow-xs backdrop-blur-xs animate-fade-in transition-all duration-300 select-text"
    >
      {/* Header Meta Bar */}
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#D8D2C7]/60">
        <div className="flex items-center gap-2">
          {/* Animated Audio Pulsing Indicator */}
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-500 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-600" />
          </span>

          <span className="text-[11px] font-mono font-semibold tracking-wider uppercase text-[#111111] flex items-center gap-1.5">
            <Mic className="w-3 h-3 text-[#111111]" />
            <span>{isListening ? 'Live Transcription' : 'Processing Voice Query'}</span>
          </span>
        </div>

        {/* Language Badge & Waveform Icon */}
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-[#EEE9DF] text-[#4A4741] border border-[#D8D2C7]/50 uppercase">
            <Globe className="w-2.5 h-2.5" />
            <span>{language}</span>
          </span>

          <span className="flex items-center gap-0.5 text-xs text-[#4A4741]">
            <Activity className="w-3.5 h-3.5 animate-pulse text-[#111111]" />
          </span>
        </div>
      </div>

      {/* Real-time Streaming Transcript Display */}
      <div className="min-h-[36px] flex items-center">
        {hasContent ? (
          <p className="text-sm sm:text-base font-editorial leading-relaxed text-[#111111]">
            {finalTranscript && (
              <span className="font-normal text-[#111111] mr-1">{finalTranscript}</span>
            )}
            {interimTranscript && (
              <span className="italic text-[#4A4741] opacity-90">{interimTranscript}</span>
            )}
            {isListening && (
              <span className="inline-block w-1.5 h-4 bg-[#111111] ml-1 -mb-0.5 animate-pulse rounded-xs" />
            )}
          </p>
        ) : (
          <p className="text-xs sm:text-sm font-sans text-[#4A4741]/80 italic flex items-center gap-2">
            <span>Listening to speech... Speak naturally to see live words stream here.</span>
          </p>
        )}
      </div>
    </div>
  );
};

export default LiveTranscription;
