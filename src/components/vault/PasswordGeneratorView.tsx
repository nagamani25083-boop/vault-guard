import React, { useState } from 'react';
import { generateSecurePassword, evaluatePasswordStrength } from '@/services/crypto';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import {
  KeyRound,
  RefreshCw,
  Copy,
  Check,
  ShieldCheck,
  Sparkles,
  Cpu,
} from 'lucide-react';
import { toast } from 'sonner';

export const PasswordGeneratorView: React.FC = () => {
  const [length, setLength] = useState(18);
  const [useUppercase, setUseUppercase] = useState(true);
  const [useLowercase, setUseLowercase] = useState(true);
  const [useNumbers, setUseNumbers] = useState(true);
  const [useSymbols, setUseSymbols] = useState(true);
  const [copied, setCopied] = useState(false);

  const [password, setPassword] = useState(() =>
    generateSecurePassword({
      length: 18,
      includeUppercase: true,
      includeLowercase: true,
      includeNumbers: true,
      includeSymbols: true,
    })
  );

  const handleGenerate = () => {
    // Enforce at least one character set
    let upper = useUppercase;
    let lower = useLowercase;
    let numbers = useNumbers;
    let symbols = useSymbols;
    if (!upper && !lower && !numbers && !symbols) {
      lower = true;
      setUseLowercase(true);
    }

    const newPass = generateSecurePassword({
      length,
      includeUppercase: upper,
      includeLowercase: lower,
      includeNumbers: numbers,
      includeSymbols: symbols,
    });
    setPassword(newPass);
    setCopied(false);
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(password);
      setCopied(true);
      toast.success('Password copied to clipboard!');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Failed to copy password.');
    }
  };

  const strength = evaluatePasswordStrength(password);

  const strengthColor = () => {
    switch (strength.score) {
      case 0:
      case 1:
        return 'bg-destructive';
      case 2:
        return 'bg-amber-500';
      case 3:
        return 'bg-blue-400';
      case 4:
      default:
        return 'bg-emerald-400';
    }
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto py-2">
      <div className="space-y-1">
        <h2 className="text-xl sm:text-2xl font-bold text-white flex items-center gap-2">
          <KeyRound className="h-5 w-5 text-purple-400" /> Password Generator
        </h2>
        <p className="text-xs text-muted-foreground">
          Generates cryptographically random keys using the browser&apos;s Web Crypto API (<code>crypto.getRandomValues</code>).
        </p>
      </div>

      <Card className="vault-card p-6 space-y-6 rounded-2xl">
        {/* Output Box */}
        <div className="space-y-2">
          <div className="p-4 rounded-xl bg-[#0B1020] border border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <span className="font-mono text-sm sm:text-base text-white break-all select-all font-semibold">
              {password}
            </span>

            <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleGenerate}
                className="h-9 px-3 rounded-xl border-border bg-[#141B2D] text-muted-foreground hover:text-white"
                title="Regenerate password"
              >
                <RefreshCw className="h-3.5 w-3.5 mr-1.5" /> Regenerate
              </Button>

              <Button
                type="button"
                size="sm"
                onClick={handleCopy}
                className="btn-vault-primary h-9 px-4 rounded-xl text-xs font-semibold"
              >
                {copied ? (
                  <>
                    <Check className="h-3.5 w-3.5 mr-1 text-emerald-300" /> Copied!
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5 mr-1" /> Copy Password
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Strength bar */}
          <div className="space-y-1 px-1">
            <div className="flex justify-between text-[11px] text-muted-foreground">
              <span>
                Strength: <strong className="text-white">{strength.label}</strong>
              </span>
              <span>{strength.feedback}</span>
            </div>
            <div className="h-1.5 w-full bg-[#0B1020] rounded-full overflow-hidden border border-border/50">
              <div
                className={`h-full transition-all duration-300 rounded-full ${strengthColor()}`}
                style={{ width: `${(strength.score / 4) * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Configuration Options */}
        <div className="space-y-5 pt-2 border-t border-border">
          {/* Length Slider */}
          <div className="space-y-3">
            <div className="flex justify-between items-center text-xs">
              <Label className="text-white font-medium">Password Length</Label>
              <div className="flex items-center gap-2">
                <span className="font-mono text-blue-400 font-bold text-sm">{length}</span>
                <span className="text-[11px] text-muted-foreground">characters</span>
              </div>
            </div>

            <Slider
              value={[length]}
              min={8}
              max={64}
              step={1}
              onValueChange={(val) => {
                setLength(val[0]);
                setPassword(
                  generateSecurePassword({
                    length: val[0],
                    includeUppercase: useUppercase,
                    includeLowercase: useLowercase,
                    includeNumbers: useNumbers,
                    includeSymbols: useSymbols,
                  })
                );
              }}
              className="py-1"
            />
          </div>

          {/* Character Toggles */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
            <div className="p-3 rounded-xl bg-[#0B1020] border border-border flex items-center justify-between">
              <label htmlFor="gen-upper" className="cursor-pointer space-y-0.5">
                <div className="font-medium text-white">Uppercase Letters</div>
                <div className="text-[11px] text-muted-foreground font-mono">A - Z</div>
              </label>
              <Checkbox
                id="gen-upper"
                checked={useUppercase}
                onCheckedChange={(c) => {
                  setUseUppercase(!!c);
                }}
              />
            </div>

            <div className="p-3 rounded-xl bg-[#0B1020] border border-border flex items-center justify-between">
              <label htmlFor="gen-lower" className="cursor-pointer space-y-0.5">
                <div className="font-medium text-white">Lowercase Letters</div>
                <div className="text-[11px] text-muted-foreground font-mono">a - z</div>
              </label>
              <Checkbox
                id="gen-lower"
                checked={useLowercase}
                onCheckedChange={(c) => {
                  setUseLowercase(!!c);
                }}
              />
            </div>

            <div className="p-3 rounded-xl bg-[#0B1020] border border-border flex items-center justify-between">
              <label htmlFor="gen-num" className="cursor-pointer space-y-0.5">
                <div className="font-medium text-white">Numbers</div>
                <div className="text-[11px] text-muted-foreground font-mono">0 - 9</div>
              </label>
              <Checkbox
                id="gen-num"
                checked={useNumbers}
                onCheckedChange={(c) => {
                  setUseNumbers(!!c);
                }}
              />
            </div>

            <div className="p-3 rounded-xl bg-[#0B1020] border border-border flex items-center justify-between">
              <label htmlFor="gen-sym" className="cursor-pointer space-y-0.5">
                <div className="font-medium text-white">Special Symbols</div>
                <div className="text-[11px] text-muted-foreground font-mono">! @ # $ % ^ &amp; *</div>
              </label>
              <Checkbox
                id="gen-sym"
                checked={useSymbols}
                onCheckedChange={(c) => {
                  setUseSymbols(!!c);
                }}
              />
            </div>
          </div>
        </div>

        {/* Security transparency footer */}
        <div className="p-3.5 rounded-xl bg-[#0B1020] border border-border text-[11px] text-muted-foreground flex items-center gap-2.5">
          <Cpu className="h-4 w-4 text-purple-400 shrink-0" />
          <span>
            Entropy is sourced directly from your operating system&apos;s cryptographically secure PRNG via{' '}
            <code className="text-white">crypto.getRandomValues</code>. No pseudo-random Math.random() is used.
          </span>
        </div>
      </Card>
    </div>
  );
};
