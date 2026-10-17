import React, { useState } from 'react';
import { useVault } from '@/contexts/VaultContext';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
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
import {
  Settings,
  Shield,
  Trash2,
  Clock,
  Download,
  Terminal,
} from 'lucide-react';
import { toast } from 'sonner';

interface SettingsViewProps {
  onOpenInspector: () => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ onOpenInspector }) => {
  const { settings, updateSettings, resetEntireVault, storedMetadata, entries } = useVault();
  const [autoLockMinutes, setAutoLockMinutes] = useState(String(settings.autoLockMinutes));
  const [confirmWipeOpen, setConfirmWipeOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const handleSaveSettings = async () => {
    setIsSaving(true);
    try {
      await updateSettings({
        autoLockMinutes: Number(autoLockMinutes),
      });
      toast.success('Inactivity auto-lock threshold updated.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleExportEncryptedBackup = () => {
    if (!storedMetadata) {
      toast.error('No stored vault data available to export.');
      return;
    }

    const exportData = {
      ...storedMetadata,
      exportedAt: new Date().toISOString(),
      note: 'Encrypted VaultGuard backup. Contains ciphertext and KDF salt only—zero plaintext passwords.',
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `vaultguard-encrypted-backup-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    toast.success('Encrypted vault backup downloaded (No plaintext contained).');
  };

  const handleConfirmWipe = async () => {
    setConfirmWipeOpen(false);
    await resetEntireVault();
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto py-2">
      <div className="space-y-1">
        <h2 className="text-xl sm:text-2xl font-bold text-white flex items-center gap-2">
          <Settings className="h-5 w-5 text-blue-400" /> Vault Settings
        </h2>
        <p className="text-xs text-muted-foreground">
          Configure security timeouts, download encrypted backups, and manage local storage.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Security & Inactivity Session */}
        <Card className="vault-card p-5 rounded-2xl space-y-4">
          <div className="space-y-1">
            <h3 className="text-sm font-semibold flex items-center gap-2 text-white">
              <Clock className="h-4 w-4 text-purple-400" /> Inactivity Auto-Lock
            </h3>
            <p className="text-xs text-muted-foreground">
              Purges in-memory keys and returns to the unlock screen after idle timeout.
            </p>
          </div>

          <div className="space-y-3 text-xs">
            <div className="space-y-1.5">
              <Label htmlFor="auto-lock-select" className="text-xs text-white">
                Lock Threshold Duration
              </Label>
              <Select value={autoLockMinutes} onValueChange={setAutoLockMinutes}>
                <SelectTrigger id="auto-lock-select" className="text-xs h-9 rounded-xl bg-[#0B1020] border-border text-white">
                  <SelectValue placeholder="Select duration" />
                </SelectTrigger>
                <SelectContent className="bg-[#141B2D] border-border text-white">
                  <SelectItem value="1">1 minute (Quick testing)</SelectItem>
                  <SelectItem value="2">2 minutes</SelectItem>
                  <SelectItem value="5">5 minutes (Default)</SelectItem>
                  <SelectItem value="15">15 minutes</SelectItem>
                  <SelectItem value="30">30 minutes</SelectItem>
                  <SelectItem value="0">Never (Disable auto-lock)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button
              size="sm"
              onClick={handleSaveSettings}
              disabled={isSaving}
              className="btn-vault-primary rounded-xl text-xs h-8 font-medium"
            >
              {isSaving ? 'Saving...' : 'Apply Timeout'}
            </Button>
          </div>
        </Card>

        {/* Cryptographic Backup & Inspector */}
        <Card className="vault-card p-5 rounded-2xl space-y-4">
          <div className="space-y-1">
            <h3 className="text-sm font-semibold flex items-center gap-2 text-white">
              <Shield className="h-4 w-4 text-emerald-400" /> Encrypted Backup &amp; Inspector
            </h3>
            <p className="text-xs text-muted-foreground">
              Export encrypted ciphertext or inspect raw IndexedDB storage.
            </p>
          </div>

          <div className="space-y-3 text-xs">
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              Backups export only the AES-256-GCM ciphertext, PBKDF2 salt, and IV. Plaintext credentials are never saved.
            </p>

            <div className="flex flex-wrap items-center gap-2 pt-1">
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportEncryptedBackup}
                className="rounded-xl text-xs h-8 border-border bg-[#141B2D] text-muted-foreground hover:text-white"
              >
                <Download className="h-3.5 w-3.5 mr-1.5 text-blue-400" /> Export Encrypted JSON
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={onOpenInspector}
                className="rounded-xl text-xs h-8 border-border bg-[#141B2D] text-muted-foreground hover:text-white"
              >
                <Terminal className="h-3.5 w-3.5 mr-1.5 text-purple-400" /> Storage Inspector
              </Button>
            </div>
          </div>
        </Card>

        {/* Danger Zone: Factory Reset */}
        <Card className="vault-card p-5 rounded-2xl space-y-3 border-destructive/30 md:col-span-2">
          <div className="space-y-1">
            <h3 className="text-sm font-semibold flex items-center gap-2 text-destructive">
              <Trash2 className="h-4 w-4" /> Danger Zone: Factory Reset
            </h3>
            <p className="text-xs text-muted-foreground">
              Completely wipe the IndexedDB vault (<code>SecureVaultDB</code>) from this browser.
            </p>
          </div>

          <div className="space-y-3 text-xs">
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              This action permanently deletes all {entries.length} stored credentials. There is no recovery once wiped.
            </p>

            <Button
              variant="destructive"
              size="sm"
              onClick={() => setConfirmWipeOpen(true)}
              className="rounded-xl text-xs h-8"
            >
              <Trash2 className="h-3.5 w-3.5 mr-1.5" /> Wipe Vault &amp; Reset DB
            </Button>
          </div>
        </Card>
      </div>

      {/* Confirmation Dialog */}
      <AlertDialog open={confirmWipeOpen} onOpenChange={setConfirmWipeOpen}>
        <AlertDialogContent className="max-w-[calc(100%-2rem)] md:max-w-md bg-[#141B2D] border-destructive/40 text-white rounded-2xl">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-destructive flex items-center gap-2">
              <Trash2 className="h-5 w-5" /> Wipe Entire Vault?
            </AlertDialogTitle>
            <AlertDialogDescription className="text-xs text-muted-foreground text-pretty">
              This will irreversibly delete <strong>SecureVaultDB</strong> from your browser&apos;s IndexedDB.
              All {entries.length} credentials will be lost.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-xl text-xs bg-[#0B1020] text-muted-foreground border-border hover:text-white">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmWipe}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90 rounded-xl text-xs"
            >
              Yes, Permanently Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
