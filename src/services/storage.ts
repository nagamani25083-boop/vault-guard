import type { StoredVaultRecord } from '@/types/vault';

const DB_NAME = 'SecureVaultDB';
const DB_VERSION = 1;
const STORE_NAME = 'vault_store';
const RECORD_ID = 'primary_vault';

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (!window.indexedDB) {
      reject(new Error('IndexedDB is not supported in this browser. Please use a modern browser.'));
      return;
    }

    const request = window.indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id' });
      }
    };

    request.onsuccess = () => {
      resolve(request.result);
    };

    request.onerror = () => {
      reject(request.error || new Error('Failed to open SecureVault IndexedDB'));
    };
  });
}

/**
 * Checks if a vault record exists in IndexedDB.
 */
export async function isVaultInitialized(): Promise<boolean> {
  try {
    const vault = await getStoredVault();
    return vault !== null;
  } catch (err) {
    console.error('Error checking vault existence:', err);
    return false;
  }
}

/**
 * Retrieves the raw encrypted vault record from IndexedDB.
 * Only encrypted ciphertext, salt, IV, and metadata are returned.
 */
export async function getStoredVault(): Promise<StoredVaultRecord | null> {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(STORE_NAME, 'readonly');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.get(RECORD_ID);

    request.onsuccess = () => {
      resolve(request.result as StoredVaultRecord || null);
    };

    request.onerror = () => {
      reject(request.error || new Error('Failed to read from IndexedDB'));
    };
  });
}

/**
 * Saves or updates the encrypted vault record in IndexedDB.
 * NEVER writes plaintext or master password.
 */
export async function saveStoredVault(record: StoredVaultRecord): Promise<void> {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(STORE_NAME, 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.put(record);

    request.onsuccess = () => {
      resolve();
    };

    request.onerror = () => {
      reject(request.error || new Error('Failed to write encrypted record to IndexedDB'));
    };
  });
}

/**
 * Completely purges the vault from IndexedDB (Factory Reset).
 */
export async function clearStoredVault(): Promise<void> {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(STORE_NAME, 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.delete(RECORD_ID);

    request.onsuccess = () => {
      resolve();
    };

    request.onerror = () => {
      reject(request.error || new Error('Failed to delete vault from IndexedDB'));
    };
  });
}

/**
 * Educational helper for B.Tech CSE Project Testing:
 * Deliberately flips bytes in the ciphertext to simulate data tampering / corruption.
 * This demonstrates AES-GCM tag verification failure (AEAD integrity protection).
 */
export async function simulateCiphertextTampering(): Promise<void> {
  const vault = await getStoredVault();
  if (!vault) throw new Error('No vault found to tamper with');

  // Flip the last two characters of the ciphertextHex
  const original = vault.ciphertextHex;
  const tampered = original.slice(0, -2) + (original.endsWith('aa') ? 'bb' : 'aa');
  
  vault.ciphertextHex = tampered;
  vault.updatedAt = new Date().toISOString();
  await saveStoredVault(vault);
}
