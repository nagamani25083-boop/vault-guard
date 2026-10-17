export type VaultCategory =
  | 'social'
  | 'work'
  | 'banking'
  | 'shopping'
  | 'academic'
  | 'developer'
  | 'other';

export interface VaultEntry {
  id: string;
  title: string;
  username: string;
  password: string;
  url?: string;
  category: VaultCategory;
  notes?: string;
  isFakeTestAccount?: boolean;
  createdAt: number;
  updatedAt: number;
}

export interface VaultSettings {
  autoLockMinutes: number; // 0 = disabled, 1, 2, 5, 15, 30
  requireConfirmationOnDelete: boolean;
  clearClipboardAfterSeconds: number; // default 30
  theme: 'dark' | 'midnight' | 'system';
}

export interface VaultPayload {
  vaultCheck: 'SECURE_VAULT_VALID_KEY';
  entries: VaultEntry[];
  settings: VaultSettings;
}

export interface StoredVaultRecord {
  id: 'primary_vault';
  version: number;
  kdf: {
    algorithm: 'PBKDF2';
    hash: 'SHA-256';
    iterations: number;
    saltHex: string;
  };
  encryption: {
    algorithm: 'AES-256-GCM';
    ivHex: string;
  };
  ciphertextHex: string;
  updatedAt: string;
  createdAt: string;
  metadata: {
    vaultName: string;
    itemCount: number;
    auditNotice: string;
  };
}

export type VaultLockState = 'loading' | 'uninitialized' | 'locked' | 'unlocked';
