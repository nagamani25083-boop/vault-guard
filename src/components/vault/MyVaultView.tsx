import React, { useState, useMemo } from 'react';
import type { VaultEntry, VaultCategory } from '@/types/vault';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Search,
  Plus,
  Eye,
  EyeOff,
  Copy,
  Check,
  MoreVertical,
  ExternalLink,
  Edit,
  Trash2,
  User,
  KeyRound,
  Sparkles,
  Layers,
  FolderLock,
  Globe,
  Briefcase,
  Landmark,
  ShoppingBag,
  GraduationCap,
  Code2,
} from 'lucide-react';
import { toast } from 'sonner';

interface MyVaultViewProps {
  entries: VaultEntry[];
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onAddPassword: () => void;
  onEditEntry: (entry: VaultEntry) => void;
  onDeleteEntryRequest: (id: string) => void;
  onLoadDemoAccounts: () => void;
}

export const MyVaultView: React.FC<MyVaultViewProps> = ({
  entries,
  searchQuery,
  onSearchChange,
  onAddPassword,
  onEditEntry,
  onDeleteEntryRequest,
  onLoadDemoAccounts,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<'all' | VaultCategory>('all');
  const [revealedPasswords, setRevealedPasswords] = useState<Record<string, boolean>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const toggleReveal = (id: string) => {
    setRevealedPasswords((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleCopy = async (text: string, label: string, keyId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(keyId);
      toast.success(`${label} copied to clipboard!`);
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      toast.error(`Failed to copy ${label}.`);
    }
  };

  // Filter entries
  const filteredEntries = useMemo(() => {
    return entries.filter((entry) => {
      const q = searchQuery.toLowerCase().trim();
      const matchesSearch =
        !q ||
        entry.title.toLowerCase().includes(q) ||
        entry.username.toLowerCase().includes(q) ||
        (entry.notes && entry.notes.toLowerCase().includes(q)) ||
        (entry.url && entry.url.toLowerCase().includes(q));

      const matchesCategory =
        selectedCategory === 'all' || entry.category === selectedCategory;

      return matchesSearch && matchesCategory;
    });
  }, [entries, searchQuery, selectedCategory]);

  const categories = [
    { id: 'all', label: 'All Items' },
    { id: 'social', label: 'Social' },
    { id: 'work', label: 'Work' },
    { id: 'banking', label: 'Banking' },
    { id: 'shopping', label: 'Shopping' },
    { id: 'academic', label: 'Academic' },
    { id: 'developer', label: 'Developer' },
  ];

  return (
    <div className="space-y-5 max-w-6xl mx-auto">
      {/* Top Toolbar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search your vault..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-9 h-9 rounded-xl bg-[#141B2D] border-border text-xs text-white focus:border-blue-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onLoadDemoAccounts}
            className="h-9 rounded-xl text-xs border-border bg-[#141B2D] text-muted-foreground hover:text-white"
          >
            <Layers className="h-3.5 w-3.5 mr-1.5 text-purple-400" /> Demo Accounts
          </Button>

          <Button
            type="button"
            size="sm"
            onClick={onAddPassword}
            className="btn-vault-primary h-9 rounded-xl text-xs font-semibold px-4"
          >
            <Plus className="h-3.5 w-3.5 mr-1.5" /> Add Password
          </Button>
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
        {categories.map((cat) => (
          <button
            key={cat.id}
            type="button"
            onClick={() => setSelectedCategory(cat.id as 'all' | VaultCategory)}
            className={`px-3 py-1.5 rounded-full text-xs whitespace-nowrap transition-all border ${
              selectedCategory === cat.id
                ? 'bg-purple-500/20 text-purple-300 border-purple-500/50 font-medium'
                : 'bg-[#141B2D] text-muted-foreground border-border hover:text-white'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between text-xs text-muted-foreground px-1">
        <span>
          Showing <strong className="text-white">{filteredEntries.length}</strong> of {entries.length} items
        </span>
        <span className="text-[11px] font-mono text-blue-400">
          AES-256-GCM Authenticated
        </span>
      </div>

      {/* Vault Card Grid */}
      {filteredEntries.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {filteredEntries.map((entry) => {
            const isRevealed = !!revealedPasswords[entry.id];
            const isUserCopied = copiedId === `${entry.id}-user`;
            const isPassCopied = copiedId === `${entry.id}-pass`;

            return (
              <Card key={entry.id} className="vault-card p-4 rounded-2xl flex flex-col justify-between space-y-3">
                {/* Header: Title, Category, Menu */}
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <h3 className="font-semibold text-sm text-white truncate">{entry.title}</h3>
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

                    {entry.url && (
                      <a
                        href={entry.url.startsWith('http') ? entry.url : `https://${entry.url}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-[11px] text-muted-foreground hover:text-blue-400 inline-flex items-center gap-1 truncate max-w-[240px] transition-colors"
                      >
                        {entry.url.replace(/^https?:\/\//, '')}
                        <ExternalLink className="h-2.5 w-2.5 shrink-0" />
                      </a>
                    )}
                  </div>

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-muted-foreground hover:text-white">
                        <MoreVertical className="h-3.5 w-3.5" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="text-xs bg-[#141B2D] border-border text-white">
                      <DropdownMenuItem onClick={() => onEditEntry(entry)} className="cursor-pointer">
                        <Edit className="h-3.5 w-3.5 mr-2 text-blue-400" /> Edit Entry
                      </DropdownMenuItem>
                      <DropdownMenuSeparator className="bg-border" />
                      <DropdownMenuItem
                        onClick={() => onDeleteEntryRequest(entry.id)}
                        className="cursor-pointer text-destructive focus:text-destructive"
                      >
                        <Trash2 className="h-3.5 w-3.5 mr-2" /> Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                {/* Data Fields */}
                <div className="space-y-2 text-xs">
                  {/* Username Row */}
                  <div className="flex items-center justify-between p-2 rounded-xl bg-[#0B1020] border border-border">
                    <div className="flex items-center gap-2 min-w-0 pr-2">
                      <User className="h-3.5 w-3.5 text-purple-400 shrink-0" />
                      <span className="font-mono text-xs text-white truncate select-all">
                        {entry.username}
                      </span>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCopy(entry.username, 'Username', `${entry.id}-user`)}
                      className="h-6 px-2 text-xs text-muted-foreground hover:text-blue-400 rounded-lg"
                      title="Copy username"
                    >
                      {isUserCopied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                    </Button>
                  </div>

                  {/* Password Row */}
                  <div className="flex items-center justify-between p-2 rounded-xl bg-[#0B1020] border border-border">
                    <div className="flex items-center gap-2 min-w-0 pr-2">
                      <KeyRound className="h-3.5 w-3.5 text-blue-400 shrink-0" />
                      {isRevealed ? (
                        <span className="font-mono text-xs text-white truncate select-all">
                          {entry.password}
                        </span>
                      ) : (
                        <span className="font-mono text-xs tracking-widest text-muted-foreground select-none">
                          ••••••••••••
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleReveal(entry.id)}
                        className="h-6 px-1.5 text-xs text-muted-foreground hover:text-white rounded-lg"
                        title={isRevealed ? 'Mask' : 'Reveal'}
                      >
                        {isRevealed ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCopy(entry.password, 'Password', `${entry.id}-pass`)}
                        className="h-6 px-1.5 text-xs text-muted-foreground hover:text-blue-400 rounded-lg"
                        title="Copy password"
                      >
                        {isPassCopied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                      </Button>
                    </div>
                  </div>

                  {/* Notes */}
                  {entry.notes && (
                    <p className="text-[11px] text-muted-foreground bg-[#0B1020]/60 border border-border/50 p-2 rounded-xl leading-relaxed">
                      {entry.notes}
                    </p>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      ) : (
        /* Empty State */
        <Card className="vault-card border-dashed p-8 text-center space-y-3 rounded-2xl">
          <div className="inline-flex p-3 rounded-2xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <FolderLock className="h-6 w-6" />
          </div>
          <div className="space-y-1">
            <h3 className="font-semibold text-sm text-white">
              {searchQuery ? 'No matching passwords' : 'No items in this category'}
            </h3>
            <p className="text-xs text-muted-foreground max-w-sm mx-auto">
              {searchQuery
                ? 'Try a different keyword or clear the search query.'
                : 'Click "Add Password" to encrypt a new credential.'}
            </p>
          </div>
          <div className="flex justify-center gap-2 pt-2">
            {searchQuery ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onSearchChange('')}
                className="rounded-xl text-xs bg-[#141B2D] border-border"
              >
                Clear Search
              </Button>
            ) : (
              <Button size="sm" onClick={onAddPassword} className="btn-vault-primary rounded-xl text-xs">
                <Plus className="h-3.5 w-3.5 mr-1" /> Add Password
              </Button>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};
