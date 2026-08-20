import React, { useEffect, useRef } from 'react';
import { AppState } from '../types';
import { ShieldAlert, Loader2 } from 'lucide-react';

interface VoiceOrbProps {
  state: AppState;
  analyser?: AnalyserNode | null;
  audioLevel?: number;
  stageLabel?: string;
  onClick?: () => void;
  compact?: boolean;
}

export const VoiceOrb: React.FC<VoiceOrbProps> = ({
  state,
  analyser = null,
  audioLevel = 0,
  stageLabel,
  onClick,
  compact = false,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animFrameRef = useRef<number | null>(null);

  const isIdle = state === 'IDLE';
  const isListening = state === 'LISTENING';
  const isTranscribing = state === 'TRANSCRIBING';
  const isRetrieving = state === 'RETRIEVING';
  const isGenerating = state === 'GENERATING';
  const isPlayingAudio = state === 'PLAYING_AUDIO';
  const isRefused = state === 'REFUSED';
  const isProcessing = isTranscribing || isRetrieving || isGenerating;

  const smoothedAudioRef = useRef<number>(0);
  const timeRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;

    const size = compact ? 180 : 280;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    ctx.scale(dpr, dpr);

    const cx = size / 2;
    const cy = size / 2;
    const R = compact ? 42 : 68;

    const bufferLength = analyser ? analyser.frequencyBinCount : 32;
    const audioDataArray = new Uint8Array(bufferLength);

    const render = () => {
      let targetAudio = 0;
      if (isListening && analyser) {
        analyser.getByteFrequencyData(audioDataArray);
        let sum = 0;
        const count = Math.min(16, audioDataArray.length);
        for (let i = 1; i < count; i++) {
          sum += audioDataArray[i];
        }
        targetAudio = Math.min(1.0, (sum / count) / 128);
      } else if (isListening) {
        targetAudio = audioLevel;
      } else if (isPlayingAudio) {
        targetAudio = 0.25 + Math.sin(Date.now() / 200) * 0.15;
      }

      smoothedAudioRef.current += (targetAudio - smoothedAudioRef.current) * 0.2;
      const sa = smoothedAudioRef.current;

      timeRef.current += isProcessing ? 0.03 : 0.015;
      const t = timeRef.current;

      ctx.clearRect(0, 0, size, size);

      // Outer Static Reference Ring
      ctx.beginPath();
      ctx.arc(cx, cy, R * 1.35, 0, Math.PI * 2);
      ctx.strokeStyle = '#D8D2C7';
      ctx.lineWidth = 1;
      ctx.stroke();

      // Precision Radians / Ticks
      const ticks = 48;
      for (let i = 0; i < ticks; i++) {
        const angle = (i / ticks) * Math.PI * 2;
        const tickLen = 2 + (isListening ? Math.sin(angle * 4 + t * 3) * sa * 12 : 1);
        const r1 = R * 1.35 + 2;
        const r2 = r1 + tickLen;
        ctx.beginPath();
        ctx.moveTo(cx + Math.cos(angle) * r1, cy + Math.sin(angle) * r1);
        ctx.lineTo(cx + Math.cos(angle) * r2, cy + Math.sin(angle) * r2);
        ctx.strokeStyle = isListening ? '#111111' : '#D8D2C7';
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // Middle Orbiting Arc (Active / Processing)
      ctx.beginPath();
      const arcStart = t * (isProcessing ? 2 : 0.8);
      const arcEnd = arcStart + Math.PI * (isProcessing ? 1.2 : 0.8);
      ctx.arc(cx, cy, R * 1.15, arcStart, arcEnd);
      ctx.strokeStyle = isListening ? '#111111' : isProcessing ? '#4A4741' : '#D8D2C7';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Inner Waveform / Solid Core
      const dynamicR = R * (1 + (isListening ? sa * 0.25 : Math.sin(t) * 0.03));
      ctx.beginPath();
      ctx.arc(cx, cy, dynamicR, 0, Math.PI * 2);
      ctx.fillStyle = isListening ? '#111111' : '#FBF9F4';
      ctx.fill();
      ctx.strokeStyle = '#111111';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      animFrameRef.current = requestAnimationFrame(render);
    };

    animFrameRef.current = requestAnimationFrame(render);

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [compact, state, analyser, audioLevel, isListening, isProcessing, isPlayingAudio]);

  return (
    <div className={`relative flex flex-col items-center justify-center select-none ${compact ? 'py-2' : 'py-4'}`}>
      <div
        onClick={onClick}
        className={`relative ${compact ? 'w-44 h-44' : 'w-64 h-64'} flex items-center justify-center cursor-pointer transition-transform active:scale-98`}
        role="button"
        tabIndex={0}
        aria-label="Voice interaction button"
      >
        <canvas ref={canvasRef} className="w-full h-full pointer-events-none" />

        {isRefused && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <ShieldAlert className="w-8 h-8 text-amber-800" />
          </div>
        )}
      </div>

      {stageLabel && isProcessing && (
        <div className="mt-2 text-center animate-fade-in">
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#EEE9DF] border border-[#D8D2C7] text-xs font-mono text-[#111111]">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-[#111111]" />
            <span>{stageLabel}</span>
          </span>
        </div>
      )}
    </div>
  );
};

export default VoiceOrb;
