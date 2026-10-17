import React, { useState } from 'react';
import { generateSecurePassword, evaluatePasswordStrength } from '@/services/crypto';
import type { PasswordGeneratorOptions } from '@/services/crypto';
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
import { Slider } from '@/components/ui/slider';
import { Checkbox } from '@/components/ui/checkbox';
import { Copy, RefreshCw, Check, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

interface PasswordGeneratorDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelectPassword?: (password: string) => void;
}

export const PasswordGeneratorDialog: React.FC<PasswordGeneratorDialogProps> = ({
  open,
  onOpenChange,
  onSelectPassword,
}) => {
  const [length, setLength] = useState(16);
  const [includeUppercase, setIncludeUppercase] = useState(true);
  const [includeLowercase, setIncludeLowercase] = useState(true);
  const [includeNumbers, setIncludeNumbers] = useState(true);
  const [includeSymbols, setIncludeSymbols] = useState(true);
  const [excludeAmbiguous, setExcludeAmbiguous] = useState(true);
  const [generatedPassword, setGeneratedPassword] = useState(() =>
    generateSecurePassword({
      length: 16,
      includeUppercase: true,
      includeLowercase: true,
      includeNumbers: true,
      includeSymbols: true,
      excludeAmbiguous: true,
    })
  );
  const [copied, setCopied] = useState(false);

  const handleRegenerate = () => {
    const opts: PasswordGeneratorOptions = {
      length,
      includeUppercase,
      includeLowercase,
      includeNumbers,
      includeSymbols,
      excludeAmbiguous,
    };
    setGeneratedPassword(generateSecurePassword(opts));
    setCopied(false);
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(generatedPassword);
      setCopied(true);
      toast.success('Password copied to clipboard.');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Failed to copy to clipboard.');
    }
  };

  const handleUse = () => {
    if (onSelectPassword) {
      onSelectPassword(generatedPassword);
    }
    onOpenChange(false);
  };

  const strength = evaluatePasswordStrength(generatedPassword);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[calc(100%-2rem)] md:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-base">
            <Sparkles className="h-4 w-4" /> Cryptographic Password Generator
          </DialogTitle>
          <DialogDescription className="text-xs text-pretty">
            Generated using <code>window.crypto.getRandomValues</code> for uniform entropy.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Result preview */}
          <div className="space-y-1.5">
            <div className="relative flex items-center">
              <Input
                readOnly
                value={generatedPassword}
                className="font-mono text-sm tracking-wider pr-20 bg-muted/30"
              />
              <div className="absolute right-1 flex items-center gap-1">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleRegenerate}
                  className="h-7 w-7 p-0"
                  title="Generate new"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleCopy}
                  className="h-7 w-7 p-0"
                  title="Copy password"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
                </Button>
              </div>
            </div>

            <div className="flex justify-between text-[11px] text-muted-foreground px-1">
              <span>Entropy Rating: <strong className="text-foreground">{strength.label}</strong></span>
              <span>{length} characters</span>
            </div>
          </div>

          {/* Length slider */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <Label>Length: {length}</Label>
              <span className="text-muted-foreground font-mono">8 – 32</span>
            </div>
            <Slider
              value={[length]}
              onValueChange={(val) => {
                setLength(val[0]);
                setGeneratedPassword(
                  generateSecurePassword({
                    length: val[0],
                    includeUppercase,
                    includeLowercase,
                    includeNumbers,
                    includeSymbols,
                    excludeAmbiguous,
                  })
                );
              }}
              min={8}
              max={32}
              step={1}
            />
          </div>

          {/* Options checkboxes */}
          <div className="grid grid-cols-2 gap-2.5 pt-1 text-xs">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="opt-upper"
                checked={includeUppercase}
                onCheckedChange={(c) => {
                  setIncludeUppercase(!!c);
                }}
              />
              <label htmlFor="opt-upper" className="cursor-pointer">Uppercase (A-Z)</label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="opt-lower"
                checked={includeLowercase}
                onCheckedChange={(c) => {
                  setIncludeLowercase(!!c);
                }}
              />
              <label htmlFor="opt-lower" className="cursor-pointer">Lowercase (a-z)</label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="opt-num"
                checked={includeNumbers}
                onCheckedChange={(c) => {
                  setIncludeNumbers(!!c);
                }}
              />
              <label htmlFor="opt-num" className="cursor-pointer">Numbers (0-9)</label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="opt-sym"
                checked={includeSymbols}
                onCheckedChange={(c) => {
                  setIncludeSymbols(!!c);
                }}
              />
              <label htmlFor="opt-sym" className="cursor-pointer">Symbols (!@#$...)</label>
            </div>

            <div className="flex items-center space-x-2 col-span-2 pt-1">
              <Checkbox
                id="opt-ambig"
                checked={excludeAmbiguous}
                onCheckedChange={(c) => {
                  setExcludeAmbiguous(!!c);
                }}
              />
              <label htmlFor="opt-ambig" className="cursor-pointer text-[11px] text-muted-foreground">
                Avoid ambiguous characters (e.g. O, 0, l, 1)
              </label>
            </div>
          </div>
        </div>

        <DialogFooter className="flex flex-col-reverse sm:flex-row gap-2">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button type="button" onClick={handleRegenerate} variant="secondary">
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" /> Re-Roll
          </Button>
          {onSelectPassword && (
            <Button type="button" onClick={handleUse}>
              Use Password
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
