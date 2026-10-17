import React, { useState } from 'react';
import type { VaultEntry } from '@/types/vault';
import { generateSecurePassword } from '@/services/crypto';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  ShieldCheck,
  ShieldAlert,
  KeyRound,
  Plus,
  Search,
  Sparkles,
  Copy,
  Check,
  Eye,
  EyeOff,
  FolderLock,
  ExternalLink,
  Layers,
  ArrowRight,
  Clock,
  RefreshCw,
  Repeat,
} from 'lucide-react';
import { toast } from 'sonner';

interface DashboardHomeProps {
  entries: VaultEntry[];
  weakCount: number;
  reusedCount: number;
  secondsUntilLock: number | null;
  onAddPassword: () => void;
  onNavigateToVault: (search?: string) => void;
  onNavigateToSecurity: () => void;
  onNavigateToGenerator: () => void;
  onEditEntry: (entry: VaultEntry) => void;
  onLoadDemoData: () => void;
}

export const DashboardHome: React.FC<DashboardHomeProps> = ({
  entries,
  weakCount,
  reusedCount,
  secondsUntilLock,
  onAddPassword,
  onNavigateToVault,
  onNavigateToSecurity,
  onNavigateToGenerator,
  onEditEntry,
  onLoadDemoData,
}) => {
  const [dashboardSearch, setDashboardSearch] = useState('');
  const [revealedIds, setRevealedIds] = useState<Record<string, boolean>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Embedded Quick Generator state
  const [quickPassword, setQuickPassword] = useState(() =>
    generateSecurePassword({ length: 16, includeUppercase: true, includeLowercase: true, includeNumbers: true, includeSymbols: true })
  );
  const [quickCopied, setQuickCopied] = useState(false);

  const handleRegenerateQuick = () => {
    setQuickPassword(
      generateSecurePassword({ length: 16, includeUppercase: true, includeLowercase: true, includeNumbers: true, includeSymbols: true })
    );
    setQuickCopied(false);
  };

  const handleCopyQuick = async () => {
    try {
      await navigator.clipboard.writeText(quickPassword);
      setQuickCopied(true);
      toast.success('Generated password copied to clipboard!');
      setTimeout(() => setQuickCopied(false), 2000);
    } catch {
      toast.error('Failed to copy password.');
    }
  };

  const toggleReveal = (id: string) => {
    setRevealedIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleCopy = async (text: string, label: string, idKey: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(idKey);
      toast.success(`${label} copied to clipboard!`);
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      toast.error(`Failed to copy ${label}.`);
    }
  };

  // Filtered recent entries (sorted by updatedAt descending, max 6)
  const recentEntries = [...entries]
    .sort((a, b) => b.updatedAt - a.updatedAt)
    .filter((e) => {
      if (!dashboardSearch.trim()) return true;
      const q = dashboardSearch.toLowerCase();
      return (
        e.title.toLowerCase().includes(q) ||
        e.username.toLowerCase().includes(q) ||
        (e.notes && e.notes.toLowerCase().includes(q))
      );
    })
    .slice(0, 6);

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Greeting & Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-[#141B2D] border border-border/80 shadow-lg relative overflow-hidden">
        {/* Subtle accent glow */}
        <div className="absolute -right-10 -top-10 w-48 h-48 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -left-10 -bottom-10 w-48 h-48 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="space-y-1.5 z-10">
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/25 text-[11px] text-purple-300 font-medium">
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>Authenticated Local Vault</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Your digital life, secured.
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground max-w-lg">
            Store, generate, and organize your credentials with zero-knowledge AES-256-GCM encryption in your browser.
          </p>
        </div>

        <div className="flex items-center gap-2.5 z-10 shrink-0">
          <Button
            onClick={onAddPassword}
            className="btn-vault-primary h-10 px-5 text-xs font-semibold rounded-xl shadow-md"
          >
            <Plus className="h-4 w-4 mr-1.5" /> Add Password
          </Button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3.5 top-3 h-4 w-4 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Search your vault..."
          value={dashboardSearch}
          onChange={(e) => setDashboardSearch(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && dashboardSearch) {
              onNavigateToVault(dashboardSearch);
            }
          }}
          className="pl-10 h-10 rounded-xl bg-[#141B2D] border-border text-xs text-white placeholder:text-muted-foreground focus:border-blue-500"
        />
      </div>

      {/* Real Summary Cards (Based strictly on actual application data) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        {/* Total Passwords */}
        <Card
          onClick={() => onNavigateToVault()}
          className="vault-card p-4 space-y-2 cursor-pointer hover:border-blue-500/40 transition-colors"
        >
          <div className="flex items-center justify-between text-muted-foreground text-xs">
            <span>Total Saved Items</span>
            <FolderLock className="h-4 w-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">{entries.length}</div>
          <span className="text-[11px] text-muted-foreground flex items-center gap-1">
            <span className="text-blue-400 font-medium">All encrypted</span> in IndexedDB
          </span>
        </Card>

        {/* Weak Passwords check */}
        <Card
          onClick={onNavigateToSecurity}
          className="vault-card p-4 space-y-2 cursor-pointer hover:border-destructive/40 transition-colors"
        >
          <div className="flex items-center justify-between text-muted-foreground text-xs">
            <span>Weak Passwords</span>
            <ShieldAlert className={`h-4 w-4 ${weakCount > 0 ? 'text-destructive' : 'text-emerald-400'}`} />
          </div>
          <div className={`text-2xl font-bold font-mono ${weakCount > 0 ? 'text-destructive' : 'text-emerald-400'}`}>
            {weakCount}
          </div>
          <span className="text-[11px] text-muted-foreground">
            {weakCount > 0 ? 'Short or low-entropy' : 'Zero weak passwords'}
          </span>
        </Card>

        {/* Reused Passwords check */}
        <Card
          onClick={onNavigateToSecurity}
          className="vault-card p-4 space-y-2 cursor-pointer hover:border-purple-500/40 transition-colors"
        >
          <div className="flex items-center justify-between text-muted-foreground text-xs">
            <span>Reused Passwords</span>
            <Repeat className="h-4 w-4 text-purple-400" />
          </div>
          <div className={`text-2xl font-bold font-mono ${reusedCount > 0 ? 'text-amber-400' : 'text-white'}`}>
            {reusedCount}
          </div>
          <span className="text-[11px] text-muted-foreground">
            {reusedCount > 0 ? 'Reused across accounts' : 'No duplicates found'}
          </span>
        </Card>

        {/* Auto-Lock Status */}
        <Card className="vault-card p-4 space-y-2">
          <div className="flex items-center justify-between text-muted-foreground text-xs">
            <span>Inactivity Lock</span>
            <Clock className="h-4 w-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-blue-400">
            {secondsUntilLock !== null ? `${Math.floor(secondsUntilLock / 60)}m ${secondsUntilLock % 60}s` : 'Active'}
          </div>
          <span className="text-[11px] text-muted-foreground">Automatic memory purge</span>
        </Card>
      </div>

      {/* Main Grid: Recent Entries + Quick Password Generator */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Recent Vault Entries */}
        <div className="lg:col-span-2 space-y-3.5">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <KeyRound className="h-4 w-4 text-purple-400" /> Recent Vault Entries
            </h2>
            {entries.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onNavigateToVault(dashboardSearch)}
                className="text-xs text-blue-400 hover:text-blue-300 h-7 px-2"
              >
                View all ({entries.length}) <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            )}
          </div>

          {entries.length === 0 ? (
            /* Empty State for New Users */
            <Card className="vault-card border-dashed p-8 text-center space-y-3 rounded-2xl">
              <div className="inline-flex p-3 rounded-2xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                <FolderLock className="h-6 w-6" />
              </div>
              <div className="space-y-1">
                <h3 className="font-semibold text-sm text-white">Your vault is empty</h3>
                <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                  Start by adding your first credential or load realistic demo accounts to explore VaultGuard.
                </p>
              </div>
              <div className="flex justify-center gap-2.5 pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onLoadDemoData}
                  className="rounded-xl text-xs border-border bg-[#141B2D] text-muted-foreground hover:text-white"
                >
                  <Layers className="h-3.5 w-3.5 mr-1 text-purple-400" /> Load Demo Accounts
                </Button>
                <Button
                  size="sm"
                  onClick={onAddPassword}
                  className="btn-vault-primary rounded-xl text-xs font-medium"
                >
                  <Plus className="h-3.5 w-3.5 mr-1" /> Add Password
                </Button>
              </div>
            </Card>
          ) : (
            /* Recent Entries Cards */
            <div className="space-y-2.5">
              {recentEntries.map((entry) => {
                const isRevealed = !!revealedIds[entry.id];
                const isUserCopied = copiedId === `${entry.id}-user`;
                const isPassCopied = copiedId === `${entry.id}-pass`;

                return (
                  <div
                    key={entry.id}
                    className="vault-card p-3.5 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                  >
                    {/* Title & metadata */}
                    <div className="min-w-0 flex-1 space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white truncate text-xs">{entry.title}</span>
                        <Badge
                          variant="outline"
                          className="text-[10px] uppercase font-mono px-1.5 py-0 border-border bg-[#0B1020] text-muted-foreground"
                        >
                          {entry.category}
                        </Badge>
                        {entry.isFakeTestAccount && (
                          <span className="text-[9px] font-mono px-1 py-0 rounded bg-purple-500/15 text-purple-300">
                            DEMO
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-muted-foreground font-mono truncate">
                        {entry.username}
                      </div>
                    </div>

                    {/* Masked Password & Controls */}
                    <div className="flex items-center gap-2 self-end sm:self-auto shrink-0">
                      <div className="px-2.5 py-1 rounded-lg bg-[#0B1020] border border-border font-mono text-[11px] min-w-[110px] text-center">
                        {isRevealed ? (
                          <span className="text-white select-all">{entry.password}</span>
                        ) : (
                          <span className="text-muted-foreground tracking-widest select-none">••••••••</span>
                        )}
                      </div>

                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleReveal(entry.id)}
                        className="h-7 w-7 p-0 text-muted-foreground hover:text-white"
                        title={isRevealed ? 'Hide' : 'Reveal'}
                      >
                        {isRevealed ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                      </Button>

                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCopy(entry.password, 'Password', `${entry.id}-pass`)}
                        className="h-7 w-7 p-0 text-muted-foreground hover:text-blue-400"
                        title="Copy password"
                      >
                        {isPassCopied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                      </Button>

                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => onEditEntry(entry)}
                        className="text-[11px] text-muted-foreground hover:text-white px-2 h-7"
                      >
                        Edit
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right 1 Col: Quick Password Generator Widget */}
        <div className="space-y-3.5">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-blue-400" /> Quick Generator
          </h2>

          <Card className="vault-card p-4 space-y-4 rounded-2xl">
            <div className="space-y-1">
              <span className="text-[11px] text-muted-foreground">Generated 16-character key:</span>
              <div className="p-2.5 rounded-xl bg-[#0B1020] border border-border font-mono text-xs text-white break-all flex items-center justify-between gap-2">
                <span className="select-all font-semibold">{quickPassword}</span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleRegenerateQuick}
                className="flex-1 text-xs h-8 rounded-xl border-border bg-[#141B2D] text-muted-foreground hover:text-white"
              >
                <RefreshCw className="h-3.5 w-3.5 mr-1.5" /> Regenerate
              </Button>
              <Button
                type="button"
                size="sm"
                onClick={handleCopyQuick}
                className="btn-vault-primary flex-1 text-xs h-8 rounded-xl font-medium"
              >
                {quickCopied ? (
                  <>
                    <Check className="h-3.5 w-3.5 mr-1 text-emerald-300" /> Copied!
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5 mr-1" /> Copy Key
                  </>
                )}
              </Button>
            </div>

            <div className="pt-2 border-t border-border flex items-center justify-between text-[11px] text-muted-foreground">
              <span>Need custom symbols or length?</span>
              <button
                type="button"
                onClick={onNavigateToGenerator}
                className="text-blue-400 hover:text-blue-300 underline font-medium"
              >
                Full Generator &rarr;
              </button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
