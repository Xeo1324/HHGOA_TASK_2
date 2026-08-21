import React from 'react';
import { Settings as SettingsIcon, Menu, BookOpen } from 'lucide-react';
import { Settings } from '../types';

interface HeaderProps {
  isOnline: boolean;
  onOpenSettings: () => void;
  onOpenMenu?: () => void;
  settings: Settings;
  onUpdateSettings: (newSettings: Partial<Settings>) => void;
}

export const Header: React.FC<HeaderProps> = ({
  isOnline,
  onOpenSettings,
  onOpenMenu,
  settings,
  onUpdateSettings,
}) => {
  return (
    <header className="w-full flex items-center justify-between px-4 sm:px-8 py-3.5 border-b border-[#D8D2C7] bg-[#FBF9F4]/90 backdrop-blur-sm sticky top-0 z-30 select-none">
      {/* Brand Identity & Menu Toggle */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMenu}
          className="w-8 h-8 rounded-md flex items-center justify-center text-[#4A4741] hover:text-[#111111] hover:bg-[#EEE9DF] border border-[#D8D2C7] transition-colors lg:hidden focus-visible:outline-none"
          title="Open navigation menu"
          aria-label="Open navigation menu"
        >
          <Menu className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-[#111111] flex items-center justify-center text-[#F7F3EA]">
            <BookOpen className="w-3.5 h-3.5 text-[#F7F3EA]" />
          </div>
          <div>
            <span className="text-xs font-semibold tracking-[0.16em] uppercase text-[#111111]">
              NOVARON
            </span>
            <span className="hidden sm:inline-block text-[11px] text-[#4A4741] ml-2 border-l border-[#D8D2C7] pl-2">
              Voice RAG & Knowledge System
            </span>
          </div>
        </div>
      </div>

      {/* Right Controls: Online Pill, Language Segment, Settings */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-[#D8D2C7] bg-[#F7F3EA] text-[11px] font-medium text-[#4A4741]">
          <span className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-emerald-600' : 'bg-amber-600'}`} />
          <span>{isOnline ? 'Connected' : 'Connecting'}</span>
        </div>

        {/* Language Segmented Control */}
        <div
          className="flex items-center rounded-md bg-[#EEE9DF] border border-[#D8D2C7] p-0.5 text-xs font-medium"
          role="radiogroup"
          aria-label="Interface Language"
        >
          <button
            onClick={() => onUpdateSettings({ language: 'en' })}
            role="radio"
            aria-checked={settings.language === 'en'}
            className={`px-2.5 py-0.5 rounded text-xs transition-all ${
              settings.language === 'en'
                ? 'bg-[#111111] text-[#F7F3EA] font-semibold shadow-xs'
                : 'text-[#4A4741] hover:text-[#111111]'
            }`}
            title="English"
          >
            EN
          </button>
          <button
            onClick={() => onUpdateSettings({ language: 'hi' })}
            role="radio"
            aria-checked={settings.language === 'hi'}
            className={`px-2.5 py-0.5 rounded text-xs transition-all ${
              settings.language === 'hi'
                ? 'bg-[#111111] text-[#F7F3EA] font-semibold shadow-xs'
                : 'text-[#4A4741] hover:text-[#111111]'
            }`}
            title="Hindi"
          >
            HI
          </button>
        </div>

        {/* Settings Button */}
        <button
          onClick={onOpenSettings}
          className="w-8 h-8 rounded-md flex items-center justify-center text-[#4A4741] hover:text-[#111111] hover:bg-[#EEE9DF] border border-[#D8D2C7] transition-all"
          title="System Settings"
          aria-label="System Settings"
        >
          <SettingsIcon className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};

export default Header;
