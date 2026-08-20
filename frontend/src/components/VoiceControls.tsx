import React from 'react';
import { Mic, Square, Keyboard, RotateCcw } from 'lucide-react';
import { AppState } from '../types';

interface VoiceControlsProps {
  state: AppState;
  onStartRecording: () => void;
  onStopRecording: () => void;
  onOpenKeyboard: () => void;
  onReset: () => void;
}

export const VoiceControls: React.FC<VoiceControlsProps> = ({
  state,
  onStartRecording,
  onStopRecording,
  onOpenKeyboard,
  onReset,
}) => {
  const isListening = state === 'LISTENING';
  const isProcessing = ['TRANSCRIBING', 'RETRIEVING', 'GENERATING'].includes(state);

  return (
    <div className="w-full flex items-center justify-center gap-4 my-4 select-none">
      {/* Type Question Button */}
      <button
        onClick={onOpenKeyboard}
        disabled={isListening || isProcessing}
        className="flex items-center gap-2 px-4 py-2 rounded-md bg-[#FBF9F4] hover:bg-[#EEE9DF] border border-[#D8D2C7] text-xs font-medium text-[#111111] transition-all disabled:opacity-30 shadow-xs"
        title="Type a text query"
      >
        <Keyboard className="w-3.5 h-3.5 text-[#4A4741]" />
        <span>Type Question</span>
      </button>

      {/* Primary Voice Mic Button */}
      <button
        onClick={isListening ? onStopRecording : onStartRecording}
        disabled={isProcessing}
        className={`w-14 h-14 rounded-full flex items-center justify-center transition-all shadow-xs ${
          isListening
            ? 'bg-[#111111] text-[#F7F3EA] ring-4 ring-[#D8D2C7] animate-pulse'
            : isProcessing
            ? 'bg-[#EEE9DF] text-[#4A4741] border border-[#D8D2C7] cursor-not-allowed'
            : 'bg-[#111111] hover:bg-[#222222] text-[#F7F3EA] hover:scale-[1.03]'
        }`}
        title={
          isListening
            ? 'Stop recording'
            : isProcessing
            ? 'Processing...'
            : 'Start speech query'
        }
      >
        {isListening ? (
          <Square className="w-4 h-4 fill-current" />
        ) : (
          <Mic className="w-5 h-5" />
        )}
      </button>

      {/* Reset Button */}
      <button
        onClick={onReset}
        disabled={isListening || isProcessing}
        className="flex items-center gap-1.5 px-3 py-2 rounded-md bg-[#FBF9F4] hover:bg-[#EEE9DF] border border-[#D8D2C7] text-xs font-medium text-[#4A4741] hover:text-[#111111] transition-all disabled:opacity-30 shadow-xs"
        title="Clear conversation"
      >
        <RotateCcw className="w-3.5 h-3.5" />
        <span>Reset</span>
      </button>
    </div>
  );
};

export default VoiceControls;
