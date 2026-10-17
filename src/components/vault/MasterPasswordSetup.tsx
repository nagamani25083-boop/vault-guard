import React, { useState } from 'react';
import { useVault } from '@/contexts/VaultContext';
import { evaluatePasswordStrength } from '@/services/crypto';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Eye, EyeOff, Shield, KeyRound, Sparkles, AlertCircle, HelpCircle, ArrowLeft, Check, Lock } from 'lucide-react';
import { DisclaimerBanner } from './DisclaimerBanner';

interface MasterPasswordSetupProps {
  onOpenInspector: () => void;
  onBackToLanding?: () => void;
}

export const MasterPasswordSetup: React.FC<MasterPasswordSetupProps> = ({
  onOpenInspector,
  onBackToLanding,
}) => {
  const { initVault, error, clearError } = useVault();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loadFakeAccounts, setLoadFakeAccounts] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const strength = evaluatePasswordStrength(password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setValidationError(null);

    if (password.length < 8) {
      setValidationError('Master password must be at least 8 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setValidationError('Passwords do not match. Please re-enter carefully.');
      return;
    }

    setIsSubmitting(true);
    try {
      await initVault(password, loadFakeAccounts);
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
    <div className="w-full max-w-lg mx-auto py-8 px-4 space-y-6">
      {onBackToLanding && (
        <button
          type="button"
          onClick={onBackToLanding}
          className="inline-flex items-center text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5 mr-1.5" /> Back to Home
        </button>
      )}

      <div className="text-center space-y-2">
        <div className="inline-flex items-center justify-center p-3.5 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-purple-600/30 border border-cyan-400/30 shadow-[0_0_20px_rgba(14,165,233,0.25)] mb-1">
          <Shield className="h-8 w-8 text-cyan-400" />
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
          Create Master Vault
        </h1>
        <p className="text-xs sm:text-sm text-muted-foreground text-pretty max-w-md mx-auto">
          Set up your master passphrase. It derives your 256-bit encryption key locally—nothing is sent to any server.
        </p>
      </div>

      <DisclaimerBanner />

      <Card className="cyber-card rounded-2xl border-border/70 overflow-hidden shadow-2xl">
        <CardHeader className="space-y-1 border-b border-border/50 pb-4">
          <CardTitle className="text-base flex items-center gap-2 text-foreground">
            <KeyRound className="h-4 w-4 text-cyan-400" /> Set Up Master Password
          </CardTitle>
          <CardDescription className="text-xs text-muted-foreground text-pretty">
            Your master password is used with <strong>PBKDF2 (100,000 rounds)</strong> to create your AES-GCM key.
            It is <strong>never saved in persistent storage</strong>.
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4 pt-5">
            {(error || validationError) && (
              <div className="p-3 rounded-xl border border-destructive/50 bg-destructive/10 text-destructive text-xs flex items-start gap-2.5">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span className="leading-snug">{error || validationError}</span>
              </div>
            )}

            <div className="space-y-1.5">
              <Label htmlFor="master-pwd" className="text-xs font-medium text-foreground">
                Master Password (min 8 chars)
              </Label>
              <div className="relative">
                <Input
                  id="master-pwd"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter a strong master password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (validationError) setValidationError(null);
                  }}
                  className="pr-10 text-sm font-mono rounded-xl bg-muted/40 border-border focus:border-cyan-500"
                  autoComplete="new-password"
                  required
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-1 top-1 h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>

              {/* Password Strength Indicator */}
              {password.length > 0 && (
                <div className="space-y-1.5 pt-1">
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

                  <div className="grid grid-cols-2 gap-1.5 pt-1 text-[10px] text-muted-foreground">
                    <span className={`flex items-center gap-1 ${password.length >= 8 ? 'text-emerald-400' : ''}`}>
                      <Check className="h-3 w-3" /> Min 8 characters
                    </span>
                    <span className={`flex items-center gap-1 ${/[A-Z]/.test(password) && /[a-z]/.test(password) ? 'text-emerald-400' : ''}`}>
                      <Check className="h-3 w-3" /> Upper &amp; lower case
                    </span>
                    <span className={`flex items-center gap-1 ${/\d/.test(password) ? 'text-emerald-400' : ''}`}>
                      <Check className="h-3 w-3" /> Number included
                    </span>
                    <span className={`flex items-center gap-1 ${/[^A-Za-z0-9]/.test(password) ? 'text-emerald-400' : ''}`}>
                      <Check className="h-3 w-3" /> Special symbol
                    </span>
                  </div>
                </div>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="confirm-pwd" className="text-xs font-medium text-foreground">
                Confirm Master Password
              </Label>
              <Input
                id="confirm-pwd"
                type={showPassword ? 'text' : 'password'}
                placeholder="Re-type master password"
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  if (validationError) setValidationError(null);
                }}
                className="text-sm font-mono rounded-xl bg-muted/40 border-border focus:border-cyan-500"
                autoComplete="new-password"
                required
              />
            </div>

            <div className="p-3 rounded-xl border border-border/80 bg-muted/30 space-y-2">
              <div className="flex items-start gap-2.5">
                <Checkbox
                  id="load-fake"
                  checked={loadFakeAccounts}
                  onCheckedChange={(checked) => setLoadFakeAccounts(!!checked)}
                  className="mt-0.5"
                />
                <div className="space-y-0.5 leading-none">
                  <label
                    htmlFor="load-fake"
                    className="text-xs font-medium cursor-pointer text-foreground flex items-center gap-1.5"
                  >
                    <Sparkles className="h-3.5 w-3.5 text-cyan-400" /> Pre-load Demo Test Accounts
                  </label>
                  <p className="text-[11px] text-muted-foreground pt-0.5">
                    Includes sample Banking, Social, Work, and Shopping credentials clearly marked as mock test data.
                  </p>
                </div>
              </div>
            </div>

            <div className="text-[11px] text-muted-foreground space-y-1 bg-card/60 border border-border/60 rounded-xl p-3">
              <div className="font-semibold text-foreground flex items-center gap-1.5">
                <HelpCircle className="h-3.5 w-3.5 text-purple-400" /> Security Tip
              </div>
              <p>
                There is no &ldquo;Forgot Password&rdquo; mechanism because nobody else possesses your encryption key.
                Be sure to remember your master password.
              </p>
            </div>
          </CardContent>

          <CardFooter className="flex flex-col sm:flex-row gap-2.5 pt-2 border-t border-border/50">
            <Button
              type="submit"
              disabled={isSubmitting || !password || !confirmPassword}
              className="btn-vault-primary rounded-xl w-full sm:flex-1 h-10 text-xs font-semibold"
            >
              {isSubmitting ? 'Deriving Key & Encrypting...' : 'Initialize & Encrypt Vault'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onOpenInspector}
              className="rounded-xl w-full sm:w-auto text-xs h-10 border-border"
            >
              Inspect Crypto
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};
