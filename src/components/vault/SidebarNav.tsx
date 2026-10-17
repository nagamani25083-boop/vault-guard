import React from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  ShieldCheck,
  LayoutDashboard,
  FolderLock,
  KeyRound,
  ShieldAlert,
  Settings,
  Lock,
  Clock,
  Terminal,
} from 'lucide-react';

export type VaultNavTab = 'dashboard' | 'vault' | 'generator' | 'security' | 'settings';

interface SidebarNavProps {
  activeTab: VaultNavTab;
  onSelectTab: (tab: VaultNavTab) => void;
  totalItems: number;
  weakCount: number;
  secondsUntilLock: number | null;
  onLockVault: () => void;
  onOpenInspector: () => void;
}

export const SidebarNav: React.FC<SidebarNavProps> = ({
  activeTab,
  onSelectTab,
  totalItems,
  weakCount,
  secondsUntilLock,
  onLockVault,
  onOpenInspector,
}) => {
  const formatTimer = (seconds: number | null) => {
    if (seconds === null) return 'Disabled';
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const navItems = [
    {
      id: 'dashboard' as VaultNavTab,
      label: 'Dashboard',
      icon: LayoutDashboard,
      badge: null,
    },
    {
      id: 'vault' as VaultNavTab,
      label: 'My Vault',
      icon: FolderLock,
      badge: totalItems,
    },
    {
      id: 'generator' as VaultNavTab,
      label: 'Password Generator',
      icon: KeyRound,
      badge: null,
    },
    {
      id: 'security' as VaultNavTab,
      label: 'Security',
      icon: ShieldAlert,
      badge: weakCount > 0 ? `${weakCount} alert${weakCount > 1 ? 's' : ''}` : null,
      badgeAlert: weakCount > 0,
    },
    {
      id: 'settings' as VaultNavTab,
      label: 'Settings',
      icon: Settings,
      badge: null,
    },
  ];

  return (
    <aside className="w-64 shrink-0 flex flex-col justify-between border-r border-border bg-[#0B1020] p-4 text-xs select-none">
      <div className="space-y-6">
        {/* Brand mark with shield icon */}
        <div className="flex items-center gap-3 px-2 py-1">
          <div className="w-9 h-9 rounded-xl gradient-purple-blue flex items-center justify-center text-white shadow-md shadow-purple-500/20">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <div className="font-extrabold text-sm tracking-tight text-white flex items-center gap-1.5">
              <span>VaultGuard</span>
            </div>
            <div className="text-[10px] text-muted-foreground font-mono flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              AES-256 Encrypted
            </div>
          </div>
        </div>

        {/* Navigation items */}
        <nav className="space-y-1">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground px-2 pb-1">
            Menu
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl transition-all text-xs ${
                  isActive
                    ? 'bg-gradient-to-r from-purple-500/20 to-blue-500/20 text-white font-medium border border-purple-500/40 shadow-sm'
                    : 'text-muted-foreground hover:text-white hover:bg-[#141B2D]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon
                    className={`h-4 w-4 ${
                      isActive ? 'text-purple-400' : 'text-muted-foreground'
                    }`}
                  />
                  <span>{item.label}</span>
                </div>

                {item.badge !== null && (
                  <Badge
                    variant="outline"
                    className={`text-[10px] font-mono px-1.5 py-0 h-4 border-0 ${
                      item.badgeAlert
                        ? 'bg-destructive/20 text-destructive'
                        : 'bg-[#1E293B] text-muted-foreground'
                    }`}
                  >
                    {item.badge}
                  </Badge>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom status and actions */}
      <div className="pt-4 border-t border-border space-y-2.5">
        {secondsUntilLock !== null && (
          <div className="p-2.5 rounded-xl bg-[#141B2D] border border-border flex items-center justify-between text-[11px]">
            <span className="text-muted-foreground flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 text-purple-400" />
              Auto-Lock
            </span>
            <span className="font-mono text-blue-400 font-semibold">
              {formatTimer(secondsUntilLock)}
            </span>
          </div>
        )}

        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onOpenInspector}
          className="w-full text-xs h-8 rounded-xl border-border bg-[#141B2D] text-muted-foreground hover:text-white hover:border-purple-500/50"
        >
          <Terminal className="h-3.5 w-3.5 mr-1.5 text-purple-400" />
          Crypto Inspector
        </Button>

        <Button
          type="button"
          size="sm"
          onClick={onLockVault}
          className="w-full text-xs h-8 rounded-xl bg-destructive/15 text-destructive hover:bg-destructive/25 border border-destructive/30"
        >
          <Lock className="h-3.5 w-3.5 mr-1.5" />
          Lock Vault
        </Button>
      </div>
    </aside>
  );
};
