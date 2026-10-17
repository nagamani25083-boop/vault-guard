import React, { useState } from 'react';
import { useVault } from '@/contexts/VaultContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Lock, Unlock, Eye, EyeOff, AlertCircle, RefreshCcw, Terminal, ArrowLeft, ShieldCheck } from 'lucide-react';
import { DisclaimerBanner } from './DisclaimerBanner';

interface MasterPasswordUnlockProps {
  onOpenInspector: () => void;
  onResetRequested: () => void;
  onBackToLanding?: () => void;
}

export const MasterPasswordUnlock: React.FC<MasterPasswordUnlockProps> = ({
  onOpenInspector,
  onResetRequested,
  onBackToLanding,
}) => {
  const { unlockVault, error, clearError, storedMetadata } = useVault();
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isDecrypting, setIsDecrypting] = useState(false);

  const handleUnlock = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    if (!password) return;

    setIsDecrypting(true);
    try {
      await unlockVault(password);
    } finally {
      setIsDecrypting(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto py-8 px-4 space-y-6">
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
        <div className="inline-flex items-center justify-center p-3.5 rounded-2xl bg-gradient-to-br from-purple-500/20 to-blue-600/30 border border-purple-400/30 shadow-[0_0_20px_rgba(139,92,246,0.25)] mb-1">
          <Lock className="h-8 w-8 text-purple-400" />
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
          Unlock SecureVault
        </h1>
        <p className="text-xs sm:text-sm text-muted-foreground text-pretty max-w-xs mx-auto">
          Enter your master password to derive the key and decrypt your saved credentials.
        </p>
      </div>

      <DisclaimerBanner compact />

      <Card className="cyber-card rounded-2xl border-border/70 overflow-hidden shadow-2xl">
        <CardHeader className="space-y-1 border-b border-border/50 pb-4">
          <CardTitle className="text-base flex items-center justify-between text-foreground">
            <span className="flex items-center gap-2">
              <Unlock className="h-4 w-4 text-purple-400" /> Master Password Login
            </span>
            {storedMetadata && (
              <span className="text-xs font-mono text-muted-foreground">
                {storedMetadata.metadata.itemCount} items
              </span>
            )}
          </CardTitle>
          <CardDescription className="text-xs text-muted-foreground text-pretty">
            Derives the 256-bit AES key using PBKDF2 and the stored random salt.
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleUnlock}>
          <CardContent className="space-y-4 pt-5">
            {error && (
              <div className="p-3 rounded-xl border border-destructive/50 bg-destructive/10 text-destructive text-xs space-y-1.5">
                <div className="flex items-start gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                  <span className="font-semibold">{error}</span>
                </div>
                <p className="text-[11px] text-muted-foreground pl-6">
                  AES-256-GCM authenticated encryption rejects invalid passwords or corrupted ciphertext.
                </p>
              </div>
            )}

            <div className="space-y-1.5">
              <Label htmlFor="unlock-pwd" className="text-xs font-medium text-foreground">
                Master Password
              </Label>
              <div className="relative">
                <Input
                  id="unlock-pwd"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your master password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (error) clearError();
                  }}
                  className="pr-10 text-sm font-mono rounded-xl bg-muted/40 border-border focus:border-purple-500"
                  autoFocus
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
            </div>

            {storedMetadata && (
              <div className="p-3 rounded-xl border border-border/80 bg-muted/20 text-[11px] text-muted-foreground space-y-1.5 font-mono">
                <div className="flex justify-between items-center">
                  <span>Storage:</span>
                  <span className="text-foreground">IndexedDB (SecureVaultDB)</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>PBKDF2 Salt:</span>
                  <span className="text-cyan-400 truncate max-w-[150px]">
                    {storedMetadata.kdf.saltHex.substring(0, 16)}...
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span>AES-GCM IV:</span>
                  <span className="text-purple-400 truncate max-w-[150px]">
                    {storedMetadata.encryption.ivHex}
                  </span>
                </div>
              </div>
            )}
          </CardContent>

          <CardFooter className="flex flex-col gap-2.5 pt-2 border-t border-border/50">
            <Button
              type="submit"
              disabled={isDecrypting || !password}
              className="btn-vault-primary rounded-xl w-full h-10 text-xs font-semibold"
            >
              {isDecrypting ? (
                <>
                  <RefreshCcw className="h-4 w-4 animate-spin mr-2" /> Decrypting with Web Crypto...
                </>
              ) : (
                'Unlock Vault'
              )}
            </Button>

            <div className="flex items-center justify-between w-full pt-1 text-xs">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={onOpenInspector}
                className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1.5 h-auto py-1 px-2"
              >
                <Terminal className="h-3.5 w-3.5 text-cyan-400" /> Inspect Ciphertext
              </Button>

              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={onResetRequested}
                className="text-xs text-muted-foreground hover:text-destructive h-auto py-1 px-2"
              >
                Reset / Wipe Database
              </Button>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};
