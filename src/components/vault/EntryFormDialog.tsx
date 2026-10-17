import React, { useState, useEffect } from 'react';
import type { VaultEntry, VaultCategory } from '@/types/vault';
import { evaluatePasswordStrength } from '@/services/crypto';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Eye,
  EyeOff,
  Sparkles,
  Key,
  Globe,
  User,
  Tag,
  FileText,
  Shield,
  Briefcase,
  Landmark,
  ShoppingBag,
  GraduationCap,
  Code2,
  MoreHorizontal,
} from 'lucide-react';
import { PasswordGeneratorDialog } from './PasswordGeneratorDialog';

interface EntryFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  entryToEdit: VaultEntry | null;
  onSave: (entryData: Omit<VaultEntry, 'id' | 'createdAt' | 'updatedAt'>) => Promise<void>;
  defaultCategory?: VaultCategory;
}

export const EntryFormDialog: React.FC<EntryFormDialogProps> = ({
  open,
  onOpenChange,
  entryToEdit,
  onSave,
  defaultCategory = 'social',
}) => {
  const [title, setTitle] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [url, setUrl] = useState('');
  const [category, setCategory] = useState<VaultCategory>(defaultCategory);
  const [notes, setNotes] = useState('');
  const [isFakeTestAccount, setIsFakeTestAccount] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [isGeneratorOpen, setIsGeneratorOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (entryToEdit) {
      setTitle(entryToEdit.title);
      setUsername(entryToEdit.username);
      setPassword(entryToEdit.password);
      setUrl(entryToEdit.url || '');
      setCategory(entryToEdit.category || 'social');
      setNotes(entryToEdit.notes || '');
      setIsFakeTestAccount(entryToEdit.isFakeTestAccount ?? true);
    } else {
      setTitle('');
      setUsername('');
      setPassword('');
      setUrl('');
      setCategory(defaultCategory);
      setNotes('');
      setIsFakeTestAccount(true);
    }
    setShowPassword(false);
  }, [entryToEdit, open, defaultCategory]);

  const strength = evaluatePasswordStrength(password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !username || !password) return;

    setIsSubmitting(true);
    try {
      await onSave({
        title: title.trim(),
        username: username.trim(),
        password,
        url: url.trim() || undefined,
        category,
        notes: notes.trim() || undefined,
        isFakeTestAccount,
      });
      onOpenChange(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  const strengthColor = () => {
    switch (strength.score) {
      case 0:
      case 1:
        return 'bg-destructive';
      case 2:
        return 'bg-amber-500';
      case 3:
        return 'bg-cyan-500';
      case 4:
      default:
        return 'bg-emerald-500';
    }
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-[calc(100%-2rem)] md:max-w-lg max-h-[90dvh] overflow-y-auto rounded-2xl cyber-card border-border/80">
          <DialogHeader>
            <DialogTitle className="text-base flex items-center gap-2 text-foreground">
              <Key className="h-4 w-4 text-cyan-400" />
              {entryToEdit ? 'Edit Password Entry' : 'Add New Password Entry'}
            </DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground text-pretty">
              Stored credentials are encrypted with AES-256-GCM and a fresh 96-bit IV before saving to IndexedDB.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label htmlFor="entry-title" className="text-xs flex items-center gap-1.5 text-foreground">
                <Tag className="h-3.5 w-3.5 text-cyan-400" /> Website / Account Name *
              </Label>
              <Input
                id="entry-title"
                placeholder="e.g. Apex National Bank or Twitter / X"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                className="text-sm rounded-xl bg-muted/30 border-border focus:border-cyan-500"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="entry-username" className="text-xs flex items-center gap-1.5 text-foreground">
                <User className="h-3.5 w-3.5 text-purple-400" /> Username / Email / ID *
              </Label>
              <Input
                id="entry-username"
                placeholder="e.g. user@domain.com or acct_num_123"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="text-sm rounded-xl bg-muted/30 border-border focus:border-cyan-500"
              />
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="entry-password" className="text-xs flex items-center gap-1.5 text-foreground">
                  <Key className="h-3.5 w-3.5 text-cyan-400" /> Password *
                </Label>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsGeneratorOpen(true)}
                  className="h-6 text-[11px] text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/10 px-2 rounded-lg"
                >
                  <Sparkles className="h-3 w-3 mr-1" /> Generator
                </Button>
              </div>
              <div className="relative">
                <Input
                  id="entry-password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter or generate password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="pr-10 font-mono text-sm rounded-xl bg-muted/30 border-border focus:border-cyan-500"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-1 top-1 h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                </Button>
              </div>

              {/* Password strength mini-meter */}
              {password.length > 0 && (
                <div className="space-y-1 pt-1">
                  <div className="flex justify-between text-[11px] text-muted-foreground">
                    <span>
                      Strength: <strong className="text-foreground">{strength.label}</strong>
                    </span>
                    <span>{strength.feedback}</span>
                  </div>
                  <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 rounded-full ${strengthColor()}`}
                      style={{ width: `${(strength.score / 4) * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="entry-category" className="text-xs text-foreground">
                  Category
                </Label>
                <Select
                  value={category}
                  onValueChange={(val: VaultCategory) => setCategory(val)}
                >
                  <SelectTrigger id="entry-category" className="text-xs h-9 rounded-xl bg-muted/30 border-border">
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#141B2D] border-border text-white">
                    <SelectItem value="social">Social &amp; Community</SelectItem>
                    <SelectItem value="work">Work &amp; Business</SelectItem>
                    <SelectItem value="banking">Banking &amp; Finance</SelectItem>
                    <SelectItem value="shopping">Shopping &amp; Retail</SelectItem>
                    <SelectItem value="academic">Academic &amp; College</SelectItem>
                    <SelectItem value="developer">Developer &amp; Tech</SelectItem>
                    <SelectItem value="other">Other Account</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="entry-url" className="text-xs flex items-center gap-1.5 text-foreground">
                  <Globe className="h-3.5 w-3.5 text-purple-400" /> Website URL (Optional)
                </Label>
                <Input
                  id="entry-url"
                  placeholder="https://..."
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="text-xs rounded-xl bg-muted/30 border-border focus:border-cyan-500"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="entry-notes" className="text-xs flex items-center gap-1.5 text-foreground">
                <FileText className="h-3.5 w-3.5 text-muted-foreground" /> Notes &amp; Hints (Encrypted)
              </Label>
              <Textarea
                id="entry-notes"
                placeholder="Security questions, PIN hints, or account notes..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                className="text-xs rounded-xl bg-muted/30 border-border focus:border-cyan-500"
              />
            </div>

            <div className="p-3 rounded-xl border border-border/80 bg-muted/20">
              <div className="flex items-start space-x-2.5">
                <Checkbox
                  id="fake-account-tag"
                  checked={isFakeTestAccount}
                  onCheckedChange={(c) => setIsFakeTestAccount(!!c)}
                  className="mt-0.5"
                />
                <label
                  htmlFor="fake-account-tag"
                  className="text-xs cursor-pointer space-y-0.5 leading-snug"
                >
                  <span className="font-medium text-foreground">Label as Demo Test Account</span>
                  <p className="text-[11px] text-muted-foreground">
                    Shows an indicator badge so testers know this is mock test data.
                  </p>
                </label>
              </div>
            </div>

            <DialogFooter className="flex flex-col-reverse sm:flex-row gap-2 pt-2 border-t border-border/50">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isSubmitting}
                className="rounded-xl text-xs h-9"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting || !title || !username || !password}
                className="btn-vault-primary rounded-xl text-xs h-9 font-semibold"
              >
                {isSubmitting ? 'Encrypting & Saving...' : entryToEdit ? 'Save Changes' : 'Encrypt & Save'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Embedded Password Generator modal */}
      <PasswordGeneratorDialog
        open={isGeneratorOpen}
        onOpenChange={setIsGeneratorOpen}
        onSelectPassword={(newPass) => {
          setPassword(newPass);
          setShowPassword(true);
        }}
      />
    </>
  );
};
