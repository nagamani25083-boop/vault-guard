import React, { useState } from 'react';
import { useVault } from '@/contexts/VaultContext';
import { LandingPage } from '@/components/landing/LandingPage';
import { MasterPasswordSetup } from '@/components/vault/MasterPasswordSetup';
import { MasterPasswordUnlock } from '@/components/vault/MasterPasswordUnlock';
import { VaultDashboard } from '@/components/vault/VaultDashboard';
import { InspectorModal } from '@/components/vault/InspectorModal';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { ShieldCheck, Loader2, Terminal, Lock, KeyRound, Sparkles, Home } from 'lucide-react';

export const VaultPage: React.FC = () => {
  const { lockState, resetEntireVault, lockVault } = useVault();
  const [isInspectorOpen, setIsInspectorOpen] = useState(false);
  const [isResetConfirmOpen, setIsResetConfirmOpen] = useState(false);
  // Show landing page by default if user is unauthenticated, but can switch directly to setup/login
  const [showLanding, setShowLanding] = useState(true);

  // If vault is already unlocked, show dashboard directly
  const isUnlocked = lockState === 'unlocked';

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col justify-between selection:bg-cyan-500/30 selection:text-white">
      {/* SaaS Top Navigation Bar */}
      <header className="border-b border-border/70 bg-card/60 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between text-xs">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setShowLanding(true)}
              className="flex items-center gap-2.5 text-foreground hover:opacity-90 transition-opacity"
            >
              <div className="w-8 h-8 rounded-xl gradient-purple-blue flex items-center justify-center text-white shadow-md shadow-purple-500/20">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <span className="font-extrabold text-sm tracking-tight gradient-text-purple-blue">
                VaultGuard
              </span>
            </button>
            <Badge variant="outline" className="hidden sm:inline-flex text-[10px] font-mono border-purple-500/30 text-purple-300 bg-purple-500/10">
              AES-256-GCM Zero-Knowledge
            </Badge>
          </div>

          {/* Right Navigation Controls */}
          <div className="flex items-center gap-2.5">
            {!isUnlocked && (
              <button
                type="button"
                onClick={() => setShowLanding(!showLanding)}
                className="hidden sm:flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors px-2 py-1"
              >
                {showLanding ? (
                  <>
                    <KeyRound className="h-3.5 w-3.5 text-purple-400" />
                    <span>{lockState === 'uninitialized' ? 'Register' : 'Login'}</span>
                  </>
                ) : (
                  <>
                    <Home className="h-3.5 w-3.5 text-blue-400" />
                    <span>Home</span>
                  </>
                )}
              </button>
            )}

            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsInspectorOpen(true)}
              className="h-8 rounded-xl text-xs border-border/80 hover:border-purple-500/50"
            >
              <Terminal className="h-3.5 w-3.5 mr-1 text-purple-400" />
              <span className="hidden sm:inline">Inspector</span>
            </Button>

            {isUnlocked ? (
              <Button
                size="sm"
                variant="outline"
                onClick={() => lockVault('Vault locked by user.')}
                className="h-8 rounded-xl text-xs border-border hover:border-destructive/50 text-destructive hover:bg-destructive/10"
              >
                <Lock className="h-3.5 w-3.5 mr-1" /> Lock
              </Button>
            ) : (
              <Button
                size="sm"
                onClick={() => setShowLanding(false)}
                className="btn-vault-primary h-8 px-3 rounded-xl text-xs font-medium"
              >
                {lockState === 'uninitialized' ? 'Get Started' : 'Unlock Vault'}
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area based on Lock State & Active View */}
      <main className="flex-1 flex flex-col justify-center">
        {lockState === 'loading' && (
          <div className="flex flex-col items-center justify-center p-12 space-y-3">
            <Loader2 className="h-7 w-7 animate-spin text-cyan-400" />
            <p className="text-xs text-muted-foreground font-mono">Initializing local Web Crypto engine &amp; IndexedDB...</p>
          </div>
        )}

        {lockState !== 'loading' && isUnlocked && (
          <VaultDashboard onOpenInspector={() => setIsInspectorOpen(true)} />
        )}

        {lockState !== 'loading' && !isUnlocked && showLanding && (
          <LandingPage
            isInitialized={lockState === 'locked'}
            onGetStarted={() => setShowLanding(false)}
            onOpenInspector={() => setIsInspectorOpen(true)}
          />
        )}

        {lockState !== 'loading' && !isUnlocked && !showLanding && lockState === 'uninitialized' && (
          <MasterPasswordSetup
            onOpenInspector={() => setIsInspectorOpen(true)}
            onBackToLanding={() => setShowLanding(true)}
          />
        )}

        {lockState !== 'loading' && !isUnlocked && !showLanding && lockState === 'locked' && (
          <MasterPasswordUnlock
            onOpenInspector={() => setIsInspectorOpen(true)}
            onResetRequested={() => setIsResetConfirmOpen(true)}
            onBackToLanding={() => setShowLanding(true)}
          />
        )}
      </main>

      {/* Modern SaaS Footer */}
      <footer className="border-t border-border/70 py-5 text-center text-xs text-muted-foreground bg-card/40 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-foreground">SecureVault</span>
            <span>&bull;</span>
            <span>Zero-Knowledge Browser Security</span>
          </div>

          <p className="font-mono text-[11px] text-muted-foreground">
            Web Crypto API (PBKDF2 100k + AES-256-GCM) &bull; IndexedDB Local
          </p>
        </div>
      </footer>

      {/* Reset Vault Confirmation Dialog */}
      <AlertDialog open={isResetConfirmOpen} onOpenChange={setIsResetConfirmOpen}>
        <AlertDialogContent className="max-w-[calc(100%-2rem)] md:max-w-md cyber-card rounded-2xl border-destructive/40">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-destructive">Reset Database &amp; Wipe Vault?</AlertDialogTitle>
            <AlertDialogDescription className="text-xs text-muted-foreground text-pretty">
              This will completely delete the IndexedDB store (<code>SecureVaultDB</code>). You will be able to set a new master password and start from scratch.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-xl text-xs">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={async () => {
                setIsResetConfirmOpen(false);
                await resetEntireVault();
              }}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90 rounded-xl text-xs"
            >
              Confirm Wipe
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Technical Inspector Modal */}
      <InspectorModal
        open={isInspectorOpen}
        onOpenChange={setIsInspectorOpen}
      />
    </div>
  );
};

export default VaultPage;
