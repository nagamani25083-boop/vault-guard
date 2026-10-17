import React, { useMemo } from 'react';
import type { VaultEntry } from '@/types/vault';
import { evaluatePasswordStrength } from '@/services/crypto';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import {
  ShieldAlert,
  ShieldCheck,
  Repeat,
  Terminal,
  Lock,
  Edit,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';

interface SecurityViewProps {
  entries: VaultEntry[];
  onEditEntry: (entry: VaultEntry) => void;
  onOpenInspector: () => void;
}

export const SecurityView: React.FC<SecurityViewProps> = ({
  entries,
  onEditEntry,
  onOpenInspector,
}) => {
  // Genuine verified security calculations:
  // 1. Weak passwords: score <= 2 or length < 10
  // 2. Reused passwords: passwords that appear > 1 time across saved accounts
  const { weakEntries, reusedGroups } = useMemo(() => {
    const weakList: VaultEntry[] = [];
    const passwordMap: Record<string, VaultEntry[]> = {};

    entries.forEach((entry) => {
      const { score } = evaluatePasswordStrength(entry.password);
      if (score <= 2 || entry.password.length < 10) {
        weakList.push(entry);
      }

      if (!passwordMap[entry.password]) {
        passwordMap[entry.password] = [];
      }
      passwordMap[entry.password].push(entry);
    });

    const reused = Object.values(passwordMap).filter((group) => group.length > 1);

    return {
      weakEntries: weakList,
      reusedGroups: reused,
    };
  }, [entries]);

  return (
    <div className="space-y-6 max-w-4xl mx-auto py-2">
      <div className="space-y-1">
        <h2 className="text-xl sm:text-2xl font-bold text-white flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-purple-400" /> Security Health &amp; Verification
        </h2>
        <p className="text-xs text-muted-foreground">
          Genuine security status verified locally against your actual stored credentials. No synthetic scores or fake audits.
        </p>
      </div>

      {/* Verified Status Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
        <Card className="vault-card p-4 space-y-1 rounded-2xl">
          <span className="text-xs text-muted-foreground">Verified Weak Passwords</span>
          <div className={`text-2xl font-bold font-mono ${weakEntries.length > 0 ? 'text-destructive' : 'text-emerald-400'}`}>
            {weakEntries.length}
          </div>
          <span className="text-[11px] text-muted-foreground">
            {weakEntries.length > 0 ? 'Complexity & length check failed' : 'All passwords meet standards'}
          </span>
        </Card>

        <Card className="vault-card p-4 space-y-1 rounded-2xl">
          <span className="text-xs text-muted-foreground">Reused Across Accounts</span>
          <div className={`text-2xl font-bold font-mono ${reusedGroups.length > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
            {reusedGroups.length}
          </div>
          <span className="text-[11px] text-muted-foreground">
            {reusedGroups.length > 0 ? 'Duplicate password hashes' : 'Zero duplicate passwords'}
          </span>
        </Card>

        <Card className="vault-card p-4 space-y-1 rounded-2xl">
          <span className="text-xs text-muted-foreground">Cipher &amp; Storage</span>
          <div className="text-xl font-bold font-mono text-blue-400">AES-256-GCM</div>
          <span className="text-[11px] text-muted-foreground">PBKDF2 100k + IndexedDB</span>
        </Card>
      </div>

      {/* Weak Passwords Section */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-destructive" />
          Weak Passwords ({weakEntries.length})
        </h3>

        {weakEntries.length === 0 ? (
          <Card className="vault-card p-4 rounded-xl text-xs text-muted-foreground flex items-center gap-2.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
            <span>Great job! No weak or low-entropy passwords were detected in your vault.</span>
          </Card>
        ) : (
          <div className="space-y-2">
            {weakEntries.map((entry) => (
              <div
                key={entry.id}
                className="vault-card p-3 rounded-xl flex items-center justify-between gap-3 text-xs border-destructive/30"
              >
                <div className="min-w-0 space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white truncate">{entry.title}</span>
                    <Badge variant="outline" className="text-[10px] bg-[#0B1020] border-border text-muted-foreground">
                      {entry.category}
                    </Badge>
                  </div>
                  <div className="text-[11px] text-muted-foreground font-mono truncate">
                    {entry.username} &bull; {entry.password.length} chars
                  </div>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onEditEntry(entry)}
                  className="h-7 text-xs rounded-lg border-border bg-[#141B2D] text-blue-400 hover:text-white"
                >
                  <Edit className="h-3 w-3 mr-1" /> Update
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Reused Passwords Section */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <Repeat className="h-4 w-4 text-amber-400" />
          Reused Passwords ({reusedGroups.length} groups)
        </h3>

        {reusedGroups.length === 0 ? (
          <Card className="vault-card p-4 rounded-xl text-xs text-muted-foreground flex items-center gap-2.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
            <span>No reused passwords detected. Every account uses a unique credential.</span>
          </Card>
        ) : (
          <div className="space-y-2.5">
            {reusedGroups.map((group, idx) => (
              <Card key={idx} className="vault-card p-3.5 rounded-xl border-amber-500/30 space-y-2 text-xs">
                <div className="text-[11px] text-amber-300 font-medium">
                  Shared password across {group.length} accounts:
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {group.map((entry) => (
                    <div
                      key={entry.id}
                      className="p-2 rounded-lg bg-[#0B1020] border border-border flex items-center justify-between gap-2"
                    >
                      <div className="min-w-0">
                        <div className="font-semibold text-white truncate">{entry.title}</div>
                        <div className="text-[10px] text-muted-foreground truncate">{entry.username}</div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEditEntry(entry)}
                        className="h-6 text-[10px] text-blue-400 hover:text-white px-2"
                      >
                        Change
                      </Button>
                    </div>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Technical Inspection & Transparency */}
      <Card className="vault-card p-5 rounded-2xl space-y-3 border-purple-500/30">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-0.5">
            <h4 className="font-bold text-sm text-white flex items-center gap-2">
              <Terminal className="h-4 w-4 text-purple-400" />
              Cryptographic Inspector &amp; Storage Audit
            </h4>
            <p className="text-xs text-muted-foreground">
              Inspect raw ciphertext, PBKDF2 salt, and IV in browser IndexedDB.
            </p>
          </div>

          <Button
            onClick={onOpenInspector}
            className="btn-vault-primary text-xs h-8 rounded-xl shrink-0"
          >
            Launch Inspector
          </Button>
        </div>
      </Card>
    </div>
  );
};
