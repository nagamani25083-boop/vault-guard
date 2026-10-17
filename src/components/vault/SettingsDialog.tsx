import React, { useState } from 'react';
import { useVault } from '@/contexts/VaultContext';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
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
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Settings, ShieldAlert, Trash2 } from 'lucide-react';

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const SettingsDialog: React.FC<SettingsDialogProps> = ({ open, onOpenChange }) => {
  const { settings, updateSettings, resetEntireVault } = useVault();
  const [autoLockMinutes, setAutoLockMinutes] = useState(String(settings.autoLockMinutes));
  const [confirmWipeOpen, setConfirmWipeOpen] = useState(false);

  const handleSave = async () => {
    await updateSettings({
      autoLockMinutes: Number(autoLockMinutes),
    });
    onOpenChange(false);
  };

  const handleConfirmWipe = async () => {
    setConfirmWipeOpen(false);
    onOpenChange(false);
    await resetEntireVault();
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-[calc(100%-2rem)] md:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-base flex items-center gap-2">
              <Settings className="h-4 w-4" /> Vault Security Settings
            </DialogTitle>
            <DialogDescription className="text-xs text-pretty">
              Configure session auto-locking and storage management.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2 text-xs">
            <div className="space-y-1.5">
              <Label htmlFor="auto-lock-select" className="text-xs">
                Inactivity Auto-Lock Timeout
              </Label>
              <Select value={autoLockMinutes} onValueChange={setAutoLockMinutes}>
                <SelectTrigger id="auto-lock-select" className="text-xs h-9">
                  <SelectValue placeholder="Select timeout" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1 minute (Recommended for testing)</SelectItem>
                  <SelectItem value="2">2 minutes</SelectItem>
                  <SelectItem value="5">5 minutes (Default)</SelectItem>
                  <SelectItem value="15">15 minutes</SelectItem>
                  <SelectItem value="0">Never (Disable auto-lock - not recommended)</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-[11px] text-muted-foreground">
                Automatically locks the vault and purges in-memory keys after no mouse or keyboard events.
              </p>
            </div>

            <div className="p-3 border border-destructive/30 bg-destructive/5 space-y-2">
              <div className="flex items-center gap-1.5 font-semibold text-destructive text-xs">
                <ShieldAlert className="h-4 w-4" /> Danger Zone: Factory Reset
              </div>
              <p className="text-[11px] text-muted-foreground">
                Permanently wipes the IndexedDB database and all stored encrypted entries from this browser.
              </p>
              <Button
                type="button"
                variant="destructive"
                size="sm"
                onClick={() => setConfirmWipeOpen(true)}
                className="text-xs h-7"
              >
                <Trash2 className="h-3 w-3 mr-1" /> Wipe Vault &amp; Reset DB
              </Button>
            </div>
          </div>

          <DialogFooter className="flex flex-col-reverse sm:flex-row gap-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="button" onClick={handleSave}>
              Save Settings
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={confirmWipeOpen} onOpenChange={setConfirmWipeOpen}>
        <AlertDialogContent className="max-w-[calc(100%-2rem)] md:max-w-lg">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-destructive flex items-center gap-2">
              <Trash2 className="h-5 w-5" /> Wipe Entire Vault?
            </AlertDialogTitle>
            <AlertDialogDescription className="text-xs text-pretty">
              This action will completely delete <strong>SecureVaultDB</strong> from browser IndexedDB.
              All fake test accounts and settings will be permanently destroyed.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmWipe}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Yes, Wipe IndexedDB
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
