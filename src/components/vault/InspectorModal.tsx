import React, { useState } from 'react';
import { useVault } from '@/contexts/VaultContext';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Database,
  Terminal,
  ShieldCheck,
  AlertTriangle,
  FileCode,
  KeyRound,
  Copy,
  Check,
  Bug,
  RefreshCw,
} from 'lucide-react';
import { simulateCiphertextTampering } from '@/services/storage';
import { toast } from 'sonner';

interface InspectorModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const InspectorModal: React.FC<InspectorModalProps> = ({ open, onOpenChange }) => {
  const { storedMetadata, refreshStoredMetadata } = useVault();
  const [copied, setCopied] = useState(false);
  const [isTampering, setIsTampering] = useState(false);

  const handleCopyRecord = async () => {
    if (!storedMetadata) return;
    try {
      await navigator.clipboard.writeText(JSON.stringify(storedMetadata, null, 2));
      setCopied(true);
      toast.success('Stored encrypted JSON copied to clipboard.');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Failed to copy to clipboard.');
    }
  };

  const handleSimulateTamper = async () => {
    setIsTampering(true);
    try {
      await simulateCiphertextTampering();
      await refreshStoredMetadata();
      toast.warning('Corrupted 1 byte in ciphertext! Next unlock attempt will fail AES-GCM tag verification.');
    } catch (err) {
      toast.error('Failed to tamper ciphertext: ' + (err instanceof Error ? err.message : 'Error'));
    } finally {
      setIsTampering(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[calc(100%-2rem)] md:max-w-3xl max-h-[90dvh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Terminal className="h-5 w-5 text-foreground" />
            <DialogTitle className="text-base">
              B.Tech CSE Project: Crypto & Storage Inspector
            </DialogTitle>
          </div>
          <DialogDescription className="text-xs text-pretty">
            Technical inspection panel to verify Web Crypto API primitives and inspect browser IndexedDB storage.
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="storage" className="w-full">
          <TabsList className="grid grid-cols-3 w-full text-xs">
            <TabsTrigger value="storage" className="text-xs">
              <Database className="h-3.5 w-3.5 mr-1.5" /> Raw Storage
            </TabsTrigger>
            <TabsTrigger value="devtools" className="text-xs">
              <FileCode className="h-3.5 w-3.5 mr-1.5" /> DevTools Guide
            </TabsTrigger>
            <TabsTrigger value="theory" className="text-xs">
              <ShieldCheck className="h-3.5 w-3.5 mr-1.5" /> CSE Theory
            </TabsTrigger>
          </TabsList>

          {/* TAB 1: Live IndexedDB Viewer */}
          <TabsContent value="storage" className="space-y-4 pt-2">
            <div className="flex flex-wrap items-center justify-between gap-2 p-3 border border-border bg-card">
              <div>
                <span className="text-xs font-semibold text-foreground block">
                  IndexedDB Target: <code>SecureVaultDB</code> → <code>vault_store</code>
                </span>
                <span className="text-[11px] text-muted-foreground">
                  Status: {storedMetadata ? 'Encrypted record saved' : 'Uninitialized'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={refreshStoredMetadata}
                  className="h-8 text-xs"
                >
                  <RefreshCw className="h-3 w-3 mr-1" /> Refresh
                </Button>
                {storedMetadata && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleCopyRecord}
                    className="h-8 text-xs"
                  >
                    {copied ? <Check className="h-3 w-3 mr-1 text-emerald-600" /> : <Copy className="h-3 w-3 mr-1" />}
                    Copy JSON
                  </Button>
                )}
              </div>
            </div>

            {storedMetadata ? (
              <div className="space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                  <div className="p-3 border border-border bg-muted/20 space-y-1">
                    <span className="font-semibold text-foreground flex items-center gap-1.5">
                      <KeyRound className="h-3.5 w-3.5" /> Key Derivation (PBKDF2)
                    </span>
                    <div className="text-[11px] space-y-0.5 text-muted-foreground font-mono">
                      <div>Algorithm: {storedMetadata.kdf.algorithm}</div>
                      <div>Hash Function: {storedMetadata.kdf.hash}</div>
                      <div>Iterations: {storedMetadata.kdf.iterations.toLocaleString()}</div>
                      <div className="truncate">Salt (128-bit): {storedMetadata.kdf.saltHex}</div>
                    </div>
                  </div>

                  <div className="p-3 border border-border bg-muted/20 space-y-1">
                    <span className="font-semibold text-foreground flex items-center gap-1.5">
                      <ShieldCheck className="h-3.5 w-3.5" /> Authenticated Encryption (AES-GCM)
                    </span>
                    <div className="text-[11px] space-y-0.5 text-muted-foreground font-mono">
                      <div>Algorithm: {storedMetadata.encryption.algorithm}</div>
                      <div>Key Length: 256 bits</div>
                      <div className="truncate">IV (96-bit fresh): {storedMetadata.encryption.ivHex}</div>
                      <div>Tag Length: 128-bit GCM Auth Tag</div>
                    </div>
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-semibold">
                    <span>Stored Raw JSON Record in IndexedDB:</span>
                    <Badge variant="outline" className="text-[10px] font-mono">
                      Ciphertext Length: {storedMetadata.ciphertextHex.length / 2} bytes
                    </Badge>
                  </div>
                  <pre className="p-3 border border-border bg-card text-[11px] font-mono overflow-x-auto max-h-52 text-foreground/90 whitespace-pre">
                    {JSON.stringify(storedMetadata, null, 2)}
                  </pre>
                  <p className="text-[11px] text-muted-foreground pt-1">
                    Notice: <strong>Zero plaintext credentials</strong> exist in this record. The ciphertext can only be decrypted when you provide the exact master password.
                  </p>
                </div>

                <div className="p-3 border border-amber-500/30 bg-amber-500/10 text-xs space-y-2">
                  <div className="flex items-center gap-1.5 font-semibold text-foreground">
                    <Bug className="h-4 w-4 text-amber-600" />
                    CSE Presentation Demo: Simulate Ciphertext Corruption (Bit-Flip)
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    Clicking this will corrupt the last byte of the stored ciphertext in IndexedDB. When you lock and attempt to unlock, AES-256-GCM&apos;s authentication tag check will immediately reject the decryption, demonstrating AEAD integrity!
                  </p>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleSimulateTamper}
                    disabled={isTampering}
                    className="text-xs h-7 border-amber-500/50"
                  >
                    Simulate 1-Byte Ciphertext Tampering
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-xs text-muted-foreground border border-dashed border-border p-6">
                No vault initialized yet. Initialize the vault to inspect the stored record.
              </div>
            )}
          </TabsContent>

          {/* TAB 2: DevTools Guide */}
          <TabsContent value="devtools" className="space-y-3 pt-2 text-xs">
            <div className="p-3 border border-border bg-card space-y-2">
              <h4 className="font-semibold text-foreground text-sm flex items-center gap-2">
                <FileCode className="h-4 w-4" /> How to verify in Chrome / Edge / Brave DevTools (F12)
              </h4>
              <ol className="list-decimal list-inside space-y-2 text-muted-foreground leading-relaxed pl-1">
                <li>
                  Press <kbd className="px-1.5 py-0.5 border border-border bg-muted font-mono text-[11px]">F12</kbd> or right-click anywhere on the page and select <strong>Inspect</strong>.
                </li>
                <li>
                  Click on the <strong>Application</strong> tab at the top toolbar of DevTools (if hidden, click the <code>&gt;&gt;</code> icon). In Firefox, this is named the <strong>Storage</strong> tab.
                </li>
                <li>
                  In the left sidebar, navigate to <strong>Storage</strong> → <strong>IndexedDB</strong>.
                </li>
                <li>
                  Click to expand <strong>SecureVaultDB</strong>, then click on <strong>vault_store</strong>.
                </li>
                <li>
                  Click on the row key <code>&ldquo;primary_vault&rdquo;</code> to view the object in the preview pane.
                </li>
                <li>
                  <strong>Verify:</strong> Observe that only <code>ciphertextHex</code>, <code>kdf</code>, and <code>encryption</code> are present. No user passwords, usernames, or master keys are visible!
                </li>
                <li>
                  Also check <strong>Local Storage</strong> and <strong>Session Storage</strong>: Verify they are completely empty of any passwords or encryption keys.
                </li>
              </ol>
            </div>
          </TabsContent>

          {/* TAB 3: Theory & CSE viva questions */}
          <TabsContent value="theory" className="space-y-3 pt-2 text-xs leading-relaxed">
            <div className="p-3 border border-border bg-card space-y-2">
              <h4 className="font-semibold text-foreground text-sm flex items-center gap-2">
                <ShieldCheck className="h-4 w-4" /> First-Year B.Tech CSE Project Cryptography Guide
              </h4>
              <div className="space-y-3 text-muted-foreground">
                <div>
                  <strong className="text-foreground">1. Why PBKDF2 instead of standard SHA-256?</strong>
                  <p>
                    A standard SHA-256 hash runs in microseconds, making offline dictionary and brute-force attacks trivial (billions of guesses per second on modern GPUs). PBKDF2 (Password-Based Key Derivation Function 2) runs 100,000 iterations with a unique 16-byte random salt, making each guess computationally expensive.
                  </p>
                </div>

                <div>
                  <strong className="text-foreground">2. Why AES-256-GCM (Galois/Counter Mode)?</strong>
                  <p>
                    AES-GCM is an Authenticated Encryption with Associated Data (AEAD) cipher. Unlike older modes like ECB or CBC without HMAC, GCM not only encrypts the data for confidentiality, but also calculates an authentication tag. If even a single bit in the ciphertext is modified or corrupted, decryption fails before exposing malformed data.
                  </p>
                </div>

                <div>
                  <strong className="text-foreground">3. Why a fresh 96-bit IV (Initialization Vector) every time?</strong>
                  <p>
                    If the same AES key and IV are reused to encrypt two different versions of the vault, an attacker can XOR the ciphertexts to reveal information about plaintext differences. Using <code>window.crypto.getRandomValues</code> generates a fresh 96-bit IV for every save operation.
                  </p>
                </div>

                <div>
                  <strong className="text-foreground">4. In-Memory Key Zeroization</strong>
                  <p>
                    The <code>CryptoKey</code> object exists strictly within JavaScript heap memory during the unlocked session. When you click Lock, close the tab, or inactivity timer expires, the key reference is discarded (set to <code>null</code>) and garbage collected.
                  </p>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};
