import React from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Shield,
  KeyRound,
  Lock,
  Cpu,
  Layers,
  Database,
  CheckCircle2,
  ArrowRight,
  Terminal,
  Sparkles,
  Zap,
} from 'lucide-react';

interface LandingPageProps {
  isInitialized: boolean;
  onGetStarted: () => void;
  onOpenInspector: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  isInitialized,
  onGetStarted,
  onOpenInspector,
}) => {
  return (
    <div className="w-full flex flex-col items-center justify-center space-y-16 py-8 md:py-16 px-4">
      {/* Hero Section */}
      <section className="w-full max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-10">
        {/* Left column: Text & CTA */}
        <div className="flex-1 space-y-6 text-center md:text-left">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-purple-500/30 bg-purple-500/10 text-xs font-medium text-purple-300">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Local Web Crypto API &bull; PBKDF2 + AES-256-GCM</span>
          </div>

          <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight leading-tight text-white">
            Zero-Knowledge Vault for the{' '}
            <span className="gradient-text-purple-blue">Modern Web</span>
          </h1>

          <p className="text-sm md:text-base text-muted-foreground max-w-xl leading-relaxed text-pretty">
            Take total control over your digital credentials. VaultGuard encrypts your passwords
            locally in browser memory using military-grade authenticated encryption.
            <strong> Zero cloud telemetry, zero server storage.</strong>
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-3 justify-center md:justify-start pt-2">
            <Button
              size="lg"
              onClick={onGetStarted}
              className="btn-vault-primary rounded-xl px-7 py-3 text-sm h-auto w-full sm:w-auto shadow-lg"
            >
              <span>{isInitialized ? 'Unlock Your Vault' : 'Get Started Free'}</span>
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>

            <Button
              variant="outline"
              size="lg"
              onClick={onOpenInspector}
              className="rounded-xl px-6 py-3 text-sm h-auto border-border hover:border-primary/50 w-full sm:w-auto"
            >
              <Terminal className="h-4 w-4 mr-2 text-primary" />
              <span>Inspect Cryptography</span>
            </Button>
          </div>

          {/* Quick trust metrics */}
          <div className="pt-4 grid grid-cols-3 gap-4 border-t border-border/60 text-xs text-muted-foreground">
            <div>
              <div className="font-bold text-foreground text-sm font-mono text-cyan-400">256-bit</div>
              <div className="text-[11px]">AES-GCM Authenticated</div>
            </div>
            <div>
              <div className="font-bold text-foreground text-sm font-mono text-purple-400">100,000</div>
              <div className="text-[11px]">PBKDF2 SHA-256 Loops</div>
            </div>
            <div>
              <div className="font-bold text-foreground text-sm font-mono text-emerald-400">100%</div>
              <div className="text-[11px]">Client-Side IndexedDB</div>
            </div>
          </div>
        </div>

        {/* Right column: Futuristic Animated Cyber Shield Illustration */}
        <div className="flex-1 w-full max-w-md flex items-center justify-center relative">
          {/* Ambient Glows */}
          <div className="absolute -inset-4 bg-gradient-to-r from-cyan-500/20 via-purple-500/20 to-blue-500/20 rounded-full blur-3xl -z-10" />

          {/* Cybernetic Shield Art */}
          <div className="w-full aspect-square max-w-[340px] cyber-card rounded-2xl p-6 relative overflow-hidden flex flex-col items-center justify-center border border-primary/20 shadow-2xl">
            {/* Grid pattern background */}
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f293710_1px,transparent_1px),linear-gradient(to_bottom,#1f293710_1px,transparent_1px)] bg-[size:1.5rem_1.5rem] opacity-30" />

            {/* Glowing Central Shield Element */}
            <div className="relative mb-5">
              <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-purple-600/30 border border-cyan-400/40 flex items-center justify-center shadow-[0_0_30px_rgba(14,165,233,0.3)]">
                <Shield className="h-12 w-12 text-cyan-400 drop-shadow-[0_0_10px_rgba(14,165,233,0.8)]" />
              </div>
              <div className="absolute -bottom-2 -right-2 p-1.5 rounded-lg bg-purple-600/90 text-white border border-purple-300/40 shadow-md">
                <Lock className="h-4 w-4" />
              </div>
            </div>

            {/* Dynamic Status Badges */}
            <div className="w-full space-y-2 relative z-10">
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-card/80 border border-border/80 text-xs">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="font-mono text-muted-foreground text-[11px]">SubtleCrypto</span>
                </div>
                <Badge variant="outline" className="text-[10px] text-emerald-400 border-emerald-500/30 bg-emerald-500/10">
                  Hardware Accelerated
                </Badge>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-lg bg-card/80 border border-border/80 text-xs">
                <div className="flex items-center gap-2">
                  <Database className="h-3.5 w-3.5 text-cyan-400" />
                  <span className="font-mono text-muted-foreground text-[11px]">IndexedDB</span>
                </div>
                <span className="text-[11px] font-mono text-cyan-400">SecureVaultDB</span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-lg bg-card/80 border border-border/80 text-xs">
                <div className="flex items-center gap-2">
                  <Zap className="h-3.5 w-3.5 text-purple-400" />
                  <span className="font-mono text-muted-foreground text-[11px]">Key State</span>
                </div>
                <span className="text-[11px] font-mono text-purple-300">In-Memory Only</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Highlights Grid */}
      <section className="w-full max-w-5xl mx-auto space-y-6">
        <div className="text-center space-y-2">
          <Badge variant="outline" className="text-xs text-primary border-primary/30">
            Enterprise Grade Architecture
          </Badge>
          <h2 className="text-2xl md:text-3xl font-bold text-foreground">
            Built for Privacy, Engineered for Speed
          </h2>
          <p className="text-xs md:text-sm text-muted-foreground max-w-lg mx-auto">
            Everything you expect from a premium password manager, running entirely client-side.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="cyber-card p-5 space-y-3 rounded-xl border border-border/70 hover:border-cyan-500/40 transition-colors">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <Shield className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-foreground text-base">Authenticated Encryption</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Every save generates a fresh random 96-bit IV and locks contents with AES-256-GCM.
              Any bit tampering causes immediate decryption rejection.
            </p>
          </div>

          <div className="cyber-card p-5 space-y-3 rounded-xl border border-border/70 hover:border-purple-500/40 transition-colors">
            <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <KeyRound className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-foreground text-base">Key Stretching (PBKDF2)</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              We stretch your master password using 100,000 iterations of SHA-256 with a unique
              128-bit salt, stopping brute-force dictionary attacks cold.
            </p>
          </div>

          <div className="cyber-card p-5 space-y-3 rounded-xl border border-border/70 hover:border-blue-500/40 transition-colors">
            <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <Layers className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-foreground text-base">Smart Categorization</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Organize credentials into Social, Work, Banking, Shopping, Academic, and Developer categories
              with instant search and quick-copy controls.
            </p>
          </div>
        </div>
      </section>

      {/* Security Architecture Visualizer */}
      <section className="w-full max-w-4xl mx-auto cyber-card p-6 md:p-8 rounded-2xl border border-border/80 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <h3 className="font-bold text-lg text-foreground flex items-center gap-2">
              <Cpu className="h-5 w-5 text-cyan-400" />
              Cryptographic Data Flow in Your Browser
            </h3>
            <p className="text-xs text-muted-foreground">
              How your master password becomes an encrypted local record.
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={onOpenInspector}
            className="text-xs rounded-lg border-primary/30 text-primary hover:bg-primary/10 shrink-0"
          >
            Launch Live Inspector
          </Button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <div className="p-3.5 rounded-xl bg-card border border-border/60 space-y-1.5">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono">Step 1</span>
            <h4 className="font-semibold text-foreground text-xs">Master Password</h4>
            <p className="text-[11px] text-muted-foreground">User inputs passphrase in memory. Never stored.</p>
          </div>

          <div className="p-3.5 rounded-xl bg-card border border-border/60 space-y-1.5">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono">Step 2</span>
            <h4 className="font-semibold text-purple-400 text-xs">PBKDF2 Key Derivation</h4>
            <p className="text-[11px] text-muted-foreground">100,000 SHA-256 iterations with 16-byte random salt.</p>
          </div>

          <div className="p-3.5 rounded-xl bg-card border border-border/60 space-y-1.5">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono">Step 3</span>
            <h4 className="font-semibold text-cyan-400 text-xs">AES-256-GCM</h4>
            <p className="text-[11px] text-muted-foreground">Fresh 96-bit IV per write + 128-bit authentication tag.</p>
          </div>

          <div className="p-3.5 rounded-xl bg-card border border-border/60 space-y-1.5">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono">Step 4</span>
            <h4 className="font-semibold text-emerald-400 text-xs">IndexedDB Storage</h4>
            <p className="text-[11px] text-muted-foreground">Only encrypted ciphertext and non-secret metadata saved.</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 text-xs text-muted-foreground border-t border-border/50">
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" /> Zero Server Telemetry
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" /> Automatic Inactivity Locking
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" /> Built-in Password Generator
          </span>
        </div>
      </section>
    </div>
  );
};
