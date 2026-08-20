import React from 'react';
import { Mic, History, Database, BookOpen } from 'lucide-react';

interface SidebarProps {
  activeTab: 'ask' | 'history' | 'sources' | 'settings';
  onSelectTab: (tab: 'ask' | 'history' | 'sources') => void;
  historyCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  historyCount,
}) => {
  const navItems = [
    {
      id: 'ask' as const,
      label: 'Ask / Query',
      icon: Mic,
      onClick: () => onSelectTab('ask'),
      isActive: activeTab === 'ask',
      badge: null,
    },
    {
      id: 'history' as const,
      label: 'Query Log',
      icon: History,
      onClick: () => onSelectTab('history'),
      isActive: activeTab === 'history',
      badge: historyCount > 0 ? historyCount : null,
    },
    {
      id: 'sources' as const,
      label: 'Corpus & Citations',
      icon: Database,
      onClick: () => onSelectTab('sources'),
      isActive: activeTab === 'sources',
      badge: null,
    },
  ];

  return (
    <aside className="hidden lg:flex flex-col justify-between w-64 bg-[#FBF9F4] border-r border-[#D8D2C7] p-6 shrink-0 select-none min-h-screen relative z-50">
      <div>
        {/* Brand Header */}
        <div className="flex items-center gap-3 mb-8 px-1">
          <div className="w-8 h-8 rounded-md bg-[#111111] flex items-center justify-center text-[#F7F3EA] shadow-xs shrink-0">
            <BookOpen className="w-4 h-4 text-[#F7F3EA]" />
          </div>
          <div>
            <h1 className="text-sm font-semibold tracking-[0.16em] text-[#111111] uppercase leading-none">
              NOVARON
            </h1>
            <p className="text-[10px] tracking-wider text-[#4A4741] uppercase mt-1">
              Voice RAG · Task 2
            </p>
          </div>
        </div>

        {/* Navigation Rail */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={item.onClick}
                className={`w-full h-10 flex items-center justify-between px-3 rounded-md text-xs font-medium transition-all ${
                  item.isActive
                    ? 'bg-[#111111] text-[#F7F3EA] font-semibold'
                    : 'text-[#4A4741] hover:text-[#111111] hover:bg-[#EEE9DF]'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </div>

                {item.badge !== null && (
                  <span className={`text-[10px] px-1.5 py-0.2 rounded ${
                    item.isActive ? 'bg-[#333333] text-[#F7F3EA]' : 'bg-[#D8D2C7] text-[#111111]'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Meta */}
      <div className="pt-4 border-t border-[#D8D2C7] text-[11px] text-[#4A4741] flex items-center justify-between">
        <span>MSMARCO-XI · 12k</span>
        <span className="text-[10px] uppercase font-mono tracking-widest text-emerald-800 font-semibold">Active</span>
      </div>
    </aside>
  );
};

export default Sidebar;
