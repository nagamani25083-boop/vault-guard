import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import type { VaultEntry, VaultSettings, VaultPayload, StoredVaultRecord, VaultLockState } from '@/types/vault';
import {
  deriveKeyFromPassword,
  encryptVaultPayload,
  decryptVaultPayload,
  getRandomBytes,
  bytesToHex,
  hexToBytes,
  SALT_BYTE_LENGTH,
  PBKDF2_ITERATIONS,
} from '@/services/crypto';
import {
  getStoredVault,
  saveStoredVault,
  clearStoredVault,
  isVaultInitialized,
} from '@/services/storage';
import { FAKE_TEST_ACCOUNTS } from '@/services/mockData';
import { toast } from 'sonner';

interface VaultContextType {
  lockState: VaultLockState;
  entries: VaultEntry[];
  settings: VaultSettings;
  storedMetadata: StoredVaultRecord | null;
  secondsUntilLock: number | null;
  error: string | null;
  clearError: () => void;
  initVault: (masterPassword: string, loadFakeAccounts?: boolean) => Promise<boolean>;
  unlockVault: (masterPassword: string) => Promise<boolean>;
  lockVault: (reason?: string) => void;
  addEntry: (entry: Omit<VaultEntry, 'id' | 'createdAt' | 'updatedAt'>) => Promise<void>;
  updateEntry: (id: string, updates: Partial<Omit<VaultEntry, 'id' | 'createdAt' | 'updatedAt'>>) => Promise<void>;
  deleteEntry: (id: string) => Promise<void>;
  loadPresetFakeAccounts: () => Promise<void>;
  updateSettings: (newSettings: Partial<VaultSettings>) => Promise<void>;
  resetEntireVault: () => Promise<void>;
  refreshStoredMetadata: () => Promise<void>;
}

const DEFAULT_SETTINGS: VaultSettings = {
  autoLockMinutes: 5,
  requireConfirmationOnDelete: true,
  clearClipboardAfterSeconds: 30,
  theme: 'dark',
};

const VaultContext = createContext<VaultContextType | undefined>(undefined);

export const VaultProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lockState, setLockState] = useState<VaultLockState>('loading');
  const [entries, setEntries] = useState<VaultEntry[]>([]);
  const [settings, setSettings] = useState<VaultSettings>(DEFAULT_SETTINGS);
  const [storedMetadata, setStoredMetadata] = useState<StoredVaultRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [secondsUntilLock, setSecondsUntilLock] = useState<number | null>(null);

  // In-memory key reference — strictly never written to disk or storage
  const activeKeyRef = useRef<CryptoKey | null>(null);
  const lastActivityRef = useRef<number>(Date.now());

  const clearError = () => setError(null);

  // Refresh stored metadata for inspector
  const refreshStoredMetadata = useCallback(async () => {
    try {
      const record = await getStoredVault();
      setStoredMetadata(record);
    } catch (err) {
      console.error('Failed to read vault record:', err);
    }
  }, []);

  // Check initial state on app boot
  useEffect(() => {
    async function checkInit() {
      try {
        const initialized = await isVaultInitialized();
        if (initialized) {
          const record = await getStoredVault();
          setStoredMetadata(record);
          setLockState('locked');
        } else {
          setLockState('uninitialized');
        }
      } catch (err) {
        console.error('Failed to check vault status:', err);
        setLockState('uninitialized');
      }
    }
    checkInit();
  }, []);

  // Lock vault and zeroize in-memory variables
  const lockVault = useCallback((reason?: string) => {
    activeKeyRef.current = null;
    setEntries([]);
    setError(null);
    setLockState('locked');
    refreshStoredMetadata();
    if (reason) {
      toast.info(reason);
    }
  }, [refreshStoredMetadata]);

  // Tab unload listener — wipe state on window unload
  useEffect(() => {
    const handleBeforeUnload = () => {
      activeKeyRef.current = null;
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  // Activity tracker for auto-lock
  useEffect(() => {
    const markActivity = () => {
      lastActivityRef.current = Date.now();
    };

    const events = ['pointerdown', 'keydown', 'scroll', 'touchstart'];
    events.forEach((evt) => window.addEventListener(evt, markActivity, { passive: true }));

    return () => {
      events.forEach((evt) => window.removeEventListener(evt, markActivity));
    };
  }, []);

  // Inactivity countdown timer
  useEffect(() => {
    if (lockState !== 'unlocked' || settings.autoLockMinutes <= 0) {
      setSecondsUntilLock(null);
      return;
    }

    const interval = setInterval(() => {
      const timeoutMs = settings.autoLockMinutes * 60 * 1000;
      const elapsed = Date.now() - lastActivityRef.current;
      const remainingMs = Math.max(0, timeoutMs - elapsed);
      const remainingSecs = Math.ceil(remainingMs / 1000);

      setSecondsUntilLock(remainingSecs);

      if (remainingMs <= 0) {
        lockVault('Vault automatically locked due to inactivity.');
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [lockState, settings.autoLockMinutes, lockVault]);

  // Internal helper to persist payload encrypted with fresh IV
  const persistEncryptedVault = async (
    newEntries: VaultEntry[],
    newSettings: VaultSettings,
    key: CryptoKey,
    saltHex: string
  ) => {
    const payload: VaultPayload = {
      vaultCheck: 'SECURE_VAULT_VALID_KEY',
      entries: newEntries,
      settings: newSettings,
    };

    // Encrypt with fresh random 96-bit IV
    const { ciphertextHex, ivHex } = await encryptVaultPayload(payload, key);

    const record: StoredVaultRecord = {
      id: 'primary_vault',
      version: 1,
      kdf: {
        algorithm: 'PBKDF2',
        hash: 'SHA-256',
        iterations: PBKDF2_ITERATIONS,
        saltHex: saltHex,
      },
      encryption: {
        algorithm: 'AES-256-GCM',
        ivHex: ivHex,
      },
      ciphertextHex: ciphertextHex,
      updatedAt: new Date().toISOString(),
      createdAt: storedMetadata?.createdAt || new Date().toISOString(),
      metadata: {
        vaultName: 'Personal SecureVault',
        itemCount: newEntries.length,
        auditNotice: 'Educational B.Tech CSE Prototype. Not professionally audited.',
      },
    };

    await saveStoredVault(record);
    setStoredMetadata(record);
  };

  // 1. First-time Vault Initialization
  const initVault = async (masterPassword: string, loadFakeAccounts = true): Promise<boolean> => {
    try {
      setError(null);
      if (!masterPassword || masterPassword.length < 8) {
        setError('Master password must be at least 8 characters long.');
        return false;
      }

      // Generate fresh random 128-bit salt
      const salt = getRandomBytes(SALT_BYTE_LENGTH);
      const saltHex = bytesToHex(salt);

      // Derive key via PBKDF2
      const key = await deriveKeyFromPassword(masterPassword, salt);
      activeKeyRef.current = key;

      const initialEntries = loadFakeAccounts ? [...FAKE_TEST_ACCOUNTS] : [];
      setEntries(initialEntries);
      setSettings(DEFAULT_SETTINGS);

      await persistEncryptedVault(initialEntries, DEFAULT_SETTINGS, key, saltHex);
      setLockState('unlocked');
      lastActivityRef.current = Date.now();
      toast.success('Vault initialized successfully with AES-256-GCM encryption!');
      return true;
    } catch (err: unknown) {
      console.error('Init error:', err);
      const msg = err instanceof Error ? err.message : 'Failed to initialize vault.';
      setError(msg);
      return false;
    }
  };

  // 2. Unlock Vault
  const unlockVault = async (masterPassword: string): Promise<boolean> => {
    try {
      setError(null);
      if (!masterPassword) {
        setError('Please enter your master password.');
        return false;
      }

      const stored = await getStoredVault();
      if (!stored) {
        setError('No vault found in browser storage. Please initialize a new vault.');
        setLockState('uninitialized');
        return false;
      }

      const salt = hexToBytes(stored.kdf.saltHex);
      // Derive key from entered password
      const key = await deriveKeyFromPassword(masterPassword, salt);

      // Attempt decryption with AES-256-GCM
      let payload: VaultPayload;
      try {
        payload = await decryptVaultPayload(stored.ciphertextHex, stored.encryption.ivHex, key);
      } catch (decryptErr) {
        console.warn('Decryption failed:', decryptErr);
        setError('Incorrect master password or corrupted ciphertext. Decryption rejected.');
        return false;
      }

      // Key is verified and valid
      activeKeyRef.current = key;
      setEntries(payload.entries || []);
      setSettings(payload.settings || DEFAULT_SETTINGS);
      setStoredMetadata(stored);
      setLockState('unlocked');
      lastActivityRef.current = Date.now();
      toast.success('Vault unlocked successfully!');
      return true;
    } catch (err: unknown) {
      console.error('Unlock error:', err);
      const msg = err instanceof Error ? err.message : 'Decryption error. Please try again.';
      setError(msg);
      return false;
    }
  };

  // 3. Add Entry
  const addEntry = async (entryData: Omit<VaultEntry, 'id' | 'createdAt' | 'updatedAt'>) => {
    if (!activeKeyRef.current || !storedMetadata) {
      toast.error('Vault is locked. Cannot save entry.');
      return;
    }

    const now = Date.now();
    const newEntry: VaultEntry = {
      ...entryData,
      id: 'entry-' + now + '-' + Math.random().toString(36).substring(2, 7),
      createdAt: now,
      updatedAt: now,
    };

    const nextEntries = [newEntry, ...entries];
    setEntries(nextEntries);
    await persistEncryptedVault(nextEntries, settings, activeKeyRef.current, storedMetadata.kdf.saltHex);
    toast.success('Login entry encrypted and saved locally.');
  };

  // 4. Update Entry
  const updateEntry = async (id: string, updates: Partial<Omit<VaultEntry, 'id' | 'createdAt' | 'updatedAt'>>) => {
    if (!activeKeyRef.current || !storedMetadata) {
      toast.error('Vault is locked. Cannot update entry.');
      return;
    }

    const nextEntries = entries.map((e) => {
      if (e.id === id) {
        return {
          ...e,
          ...updates,
          updatedAt: Date.now(),
        };
      }
      return e;
    });

    setEntries(nextEntries);
    await persistEncryptedVault(nextEntries, settings, activeKeyRef.current, storedMetadata.kdf.saltHex);
    toast.success('Entry updated and re-encrypted with fresh IV.');
  };

  // 5. Delete Entry
  const deleteEntry = async (id: string) => {
    if (!activeKeyRef.current || !storedMetadata) {
      toast.error('Vault is locked. Cannot delete entry.');
      return;
    }

    const nextEntries = entries.filter((e) => e.id !== id);
    setEntries(nextEntries);
    await persistEncryptedVault(nextEntries, settings, activeKeyRef.current, storedMetadata.kdf.saltHex);
    toast.success('Entry deleted and vault re-encrypted.');
  };

  // 6. Load Preset Fake Accounts
  const loadPresetFakeAccounts = async () => {
    if (!activeKeyRef.current || !storedMetadata) {
      toast.error('Vault is locked.');
      return;
    }

    const existingIds = new Set(entries.map((e) => e.title.toLowerCase()));
    const newFakes = FAKE_TEST_ACCOUNTS.filter((f) => !existingIds.has(f.title.toLowerCase()));

    if (newFakes.length === 0) {
      toast.info('All preset test accounts are already present in the vault.');
      return;
    }

    const nextEntries = [...newFakes, ...entries];
    setEntries(nextEntries);
    await persistEncryptedVault(nextEntries, settings, activeKeyRef.current, storedMetadata.kdf.saltHex);
    toast.success(`Loaded ${newFakes.length} fake test accounts for testing.`);
  };

  // 7. Update Settings
  const updateSettings = async (newSettings: Partial<VaultSettings>) => {
    if (!activeKeyRef.current || !storedMetadata) return;
    const merged = { ...settings, ...newSettings };
    setSettings(merged);
    await persistEncryptedVault(entries, merged, activeKeyRef.current, storedMetadata.kdf.saltHex);
    toast.success('Vault settings updated.');
  };

  // 8. Wipe / Reset entire vault
  const resetEntireVault = async () => {
    try {
      await clearStoredVault();
      activeKeyRef.current = null;
      setEntries([]);
      setStoredMetadata(null);
      setError(null);
      setLockState('uninitialized');
      toast.success('Vault reset complete. IndexedDB wiped clean.');
    } catch (err) {
      console.error('Reset error:', err);
      toast.error('Failed to wipe IndexedDB.');
    }
  };

  return (
    <VaultContext.Provider
      value={{
        lockState,
        entries,
        settings,
        storedMetadata,
        secondsUntilLock,
        error,
        clearError,
        initVault,
        unlockVault,
        lockVault,
        addEntry,
        updateEntry,
        deleteEntry,
        loadPresetFakeAccounts,
        updateSettings,
        resetEntireVault,
        refreshStoredMetadata,
      }}
    >
      {children}
    </VaultContext.Provider>
  );
};

export const useVault = (): VaultContextType => {
  const context = useContext(VaultContext);
  if (!context) {
    throw new Error('useVault must be used within a VaultProvider');
  }
  return context;
};
