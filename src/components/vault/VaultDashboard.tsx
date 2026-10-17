import React, { useState, useMemo } from 'react';
import { useVault } from '@/contexts/VaultContext';
import type { VaultEntry } from '@/types/vault';
import { evaluatePasswordStrength } from '@/services/crypto';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
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
  Menu,
  ShieldCheck,
  Plus,
  Lock,
  Terminal,
  FolderLock,
  LayoutDashboard,
  KeyRound,
  ShieldAlert,
  Settings,
} from 'lucide-react';
import { SidebarNav, type VaultNavTab } from './SidebarNav';
import { DashboardHome } from './DashboardHome';
import { MyVaultView } from './MyVaultView';
import { PasswordGeneratorView } from './PasswordGeneratorView';
import { SecurityView } from './SecurityView';
import { SettingsView } from './SettingsView';
import { EntryFormDialog } from './EntryFormDialog';
import { DisclaimerBanner } from './DisclaimerBanner';

interface VaultDashboardProps {
  onOpenInspector: () => void;
}

export const VaultDashboard: React.FC<VaultDashboardProps> = ({ onOpenInspector }) => {
  const {
    entries,
    lockVault,
    deleteEntry,
    addEntry,
    updateEntry,
    loadPresetFakeAccounts,
    secondsUntilLock,
  } = useVault();

  const [activeTab, setActiveTab] = useState<VaultNavTab>('dashboard');
  const [vaultSearchQuery, setVaultSearchQuery] = useState('');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Dialog states
  const [isEntryDialogOpen, setIsEntryDialogOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState<VaultEntry | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Real security metrics
  const { weakCount, reusedCount } = useMemo(() => {
    let weak = 0;
    const passwordMap: Record<string, number> = {};

    entries.forEach((e) => {
      const { score } = evaluatePasswordStrength(e.password);
      if (score <= 2 || e.password.length < 10) weak++;

      passwordMap[e.password] = (passwordMap[e.password] || 0) + 1;
    });

    const reused = Object.values(passwordMap).filter((cnt) => cnt > 1).length;

    return { weakCount: weak, reusedCount: reused };
  }, [entries]);

  const handleEditEntry = (entry: VaultEntry) => {
    setEditingEntry(entry);
    setIsEntryDialogOpen(true);
  };

  const handleAddPassword = () => {
    setEditingEntry(null);
    setIsEntryDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (deletingId) {
      await deleteEntry(deletingId);
      setDeletingId(null);
    }
  };

  const handleNavigateToVault = (search?: string) => {
    if (search !== undefined) setVaultSearchQuery(search);
    setActiveTab('vault');
  };

  return (
    <div className="flex-1 flex min-h-[calc(100vh-3.5rem)] bg-[#0B1020]">
      {/* Fixed Desktop Sidebar */}
      <div className="hidden md:block">
        <SidebarNav
          activeTab={activeTab}
          onSelectTab={setActiveTab}
          totalItems={entries.length}
          weakCount={weakCount}
          secondsUntilLock={secondsUntilLock}
          onLockVault={() => lockVault('Vault locked by user.')}
          onOpenInspector={onOpenInspector}
        />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 min-w-0 flex flex-col">
        {/* Mobile Top Bar */}
        <div className="md:hidden flex items-center justify-between p-3.5 border-b border-border bg-[#0B1020]">
          <div className="flex items-center gap-2.5">
            <Sheet open={isMobileMenuOpen} onOpenChange={setIsMobileMenuOpen}>
              <SheetTrigger asChild>
                <Button variant="outline" size="sm" className="h-8 w-8 p-0 rounded-xl bg-[#141B2D] border-border">
                  <Menu className="h-4 w-4" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-72 bg-[#0B1020] border-r border-border p-4 text-xs">
                <SheetHeader className="text-left pb-3 border-b border-border">
                  <SheetTitle className="text-sm font-bold flex items-center gap-2 text-white">
                    <div className="w-7 h-7 rounded-lg gradient-purple-blue flex items-center justify-center text-white">
                      <ShieldCheck className="h-4 w-4" />
                    </div>
                    <span>VaultGuard</span>
                  </SheetTitle>
                </SheetHeader>

                <div className="space-y-1.5 py-4">
                  {[
                    { id: 'dashboard' as VaultNavTab, label: 'Dashboard', icon: LayoutDashboard },
                    { id: 'vault' as VaultNavTab, label: 'My Vault', icon: FolderLock },
                    { id: 'generator' as VaultNavTab, label: 'Password Generator', icon: KeyRound },
                    { id: 'security' as VaultNavTab, label: 'Security', icon: ShieldAlert },
                    { id: 'settings' as VaultNavTab, label: 'Settings', icon: Settings },
                  ].map((item) => {
                    const Icon = item.icon;
                    const isActive = activeTab === item.id;
                    return (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => {
                          setActiveTab(item.id);
                          setIsMobileMenuOpen(false);
                        }}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all text-xs ${
                          isActive
                            ? 'bg-purple-500/20 text-white font-medium border border-purple-500/40'
                            : 'text-muted-foreground hover:text-white'
                        }`}
                      >
                        <Icon className="h-4 w-4" />
                        <span>{item.label}</span>
                      </button>
                    );
                  })}
                </div>

                <div className="pt-4 border-t border-border space-y-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setIsMobileMenuOpen(false);
                      onOpenInspector();
                    }}
                    className="w-full text-xs h-8 rounded-xl bg-[#141B2D] border-border text-muted-foreground hover:text-white"
                  >
                    <Terminal className="h-3.5 w-3.5 mr-1.5 text-purple-400" /> Inspector
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    onClick={() => {
                      setIsMobileMenuOpen(false);
                      lockVault('Vault locked.');
                    }}
                    className="w-full text-xs h-8 rounded-xl bg-destructive/20 text-destructive hover:bg-destructive/30"
                  >
                    <Lock className="h-3.5 w-3.5 mr-1.5" /> Lock Vault
                  </Button>
                </div>
              </SheetContent>
            </Sheet>

            <span className="font-bold text-sm text-white">VaultGuard</span>
          </div>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              size="sm"
              onClick={handleAddPassword}
              className="btn-vault-primary h-8 px-3 text-xs rounded-xl font-medium"
            >
              <Plus className="h-3.5 w-3.5 mr-1" /> Add
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => lockVault()}
              className="h-8 px-2 text-xs rounded-xl bg-[#141B2D] border-border text-muted-foreground hover:text-white"
            >
              <Lock className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>

        {/* Scrollable View Container */}
        <div className="flex-1 p-4 md:p-6 overflow-y-auto space-y-4">
          <DisclaimerBanner compact />

          {activeTab === 'dashboard' && (
            <DashboardHome
              entries={entries}
              weakCount={weakCount}
              reusedCount={reusedCount}
              secondsUntilLock={secondsUntilLock}
              onAddPassword={handleAddPassword}
              onNavigateToVault={handleNavigateToVault}
              onNavigateToSecurity={() => setActiveTab('security')}
              onNavigateToGenerator={() => setActiveTab('generator')}
              onEditEntry={handleEditEntry}
              onLoadDemoData={loadPresetFakeAccounts}
            />
          )}

          {activeTab === 'vault' && (
            <MyVaultView
              entries={entries}
              searchQuery={vaultSearchQuery}
              onSearchChange={setVaultSearchQuery}
              onAddPassword={handleAddPassword}
              onEditEntry={handleEditEntry}
              onDeleteEntryRequest={(id) => setDeletingId(id)}
              onLoadDemoAccounts={loadPresetFakeAccounts}
            />
          )}

          {activeTab === 'generator' && <PasswordGeneratorView />}

          {activeTab === 'security' && (
            <SecurityView
              entries={entries}
              onEditEntry={handleEditEntry}
              onOpenInspector={onOpenInspector}
            />
          )}

          {activeTab === 'settings' && <SettingsView onOpenInspector={onOpenInspector} />}
        </div>
      </div>

      {/* Delete Confirmation Alert Dialog */}
      <AlertDialog open={!!deletingId} onOpenChange={(open) => !open && setDeletingId(null)}>
        <AlertDialogContent className="max-w-[calc(100%-2rem)] md:max-w-md bg-[#141B2D] border-border text-white rounded-2xl">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-base text-white">Delete Password Entry?</AlertDialogTitle>
            <AlertDialogDescription className="text-xs text-muted-foreground text-pretty">
              This entry will be permanently removed from memory and re-encrypted in IndexedDB with a fresh IV.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-xl text-xs bg-[#0B1020] text-muted-foreground border-border hover:text-white">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90 rounded-xl text-xs"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Add / Edit Entry Dialog */}
      <EntryFormDialog
        open={isEntryDialogOpen}
        onOpenChange={setIsEntryDialogOpen}
        entryToEdit={editingEntry}
        onSave={async (data) => {
          if (editingEntry) {
            await updateEntry(editingEntry.id, data);
          } else {
            await addEntry(data);
          }
        }}
      />
    </div>
  );
};
