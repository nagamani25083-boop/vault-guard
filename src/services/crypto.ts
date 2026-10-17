import type { VaultPayload } from '@/types/vault';

// Constants for cryptographic standards
export const PBKDF2_ITERATIONS = 100000; // OWASP recommended baseline
export const SALT_BYTE_LENGTH = 16; // 128-bit salt
export const IV_BYTE_LENGTH = 12; // 96-bit IV standard for AES-GCM
export const KEY_BYTE_LENGTH = 32; // 256-bit AES key

// Helper: Convert ArrayBuffer/Uint8Array to Hex string
export function bytesToHex(bytes: Uint8Array): string {
  let hex = '';
  for (let i = 0; i < bytes.length; i++) {
    hex += bytes[i].toString(16).padStart(2, '0');
  }
  return hex;
}

// Helper: Convert Hex string to Uint8Array
export function hexToBytes(hex: string): Uint8Array {
  const cleanHex = hex.trim();
  if (cleanHex.length % 2 !== 0) {
    throw new Error('Invalid hexadecimal string length');
  }
  const bytes = new Uint8Array(cleanHex.length / 2);
  for (let i = 0; i < cleanHex.length; i += 2) {
    bytes[i / 2] = parseInt(cleanHex.substring(i, i + 2), 16);
  }
  return bytes;
}

// Generate cryptographically random bytes
export function getRandomBytes(length: number): Uint8Array {
  const array = new Uint8Array(length);
  window.crypto.getRandomValues(array);
  return array;
}

/**
 * Derives a 256-bit AES-GCM CryptoKey from a master password and salt using PBKDF2 with SHA-256.
 * Standard Web Crypto API SubtleCrypto is strictly used.
 */
export async function deriveKeyFromPassword(password: string, salt: Uint8Array): Promise<CryptoKey> {
  const encoder = new TextEncoder();
  const passwordKey = await window.crypto.subtle.importKey(
    'raw',
    encoder.encode(password),
    { name: 'PBKDF2' },
    false,
    ['deriveKey']
  );

  const derivedKey = await window.crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt: salt as unknown as ArrayBuffer,
      iterations: PBKDF2_ITERATIONS,
      hash: 'SHA-256',
    },
    passwordKey,
    {
      name: 'AES-GCM',
      length: 256,
    },
    false, // Non-extractable: key cannot be exported or leaked outside memory
    ['encrypt', 'decrypt']
  );

  return derivedKey;
}

/**
 * Encrypts a VaultPayload using AES-256-GCM with a fresh random 96-bit IV.
 * Returns the ciphertext (including GCM authentication tag) and IV as hex strings.
 */
export async function encryptVaultPayload(
  payload: VaultPayload,
  key: CryptoKey
): Promise<{ ciphertextHex: string; ivHex: string }> {
  const encoder = new TextEncoder();
  const iv = getRandomBytes(IV_BYTE_LENGTH);
  const plaintextBytes = encoder.encode(JSON.stringify(payload));

  const cipherBuffer = await window.crypto.subtle.encrypt(
    {
      name: 'AES-GCM',
      iv: iv as unknown as ArrayBuffer,
      tagLength: 128, // 128-bit authentication tag
    },
    key,
    plaintextBytes
  );

  return {
    ciphertextHex: bytesToHex(new Uint8Array(cipherBuffer)),
    ivHex: bytesToHex(iv),
  };
}

/**
 * Decrypts ciphertext using AES-256-GCM.
 * If the master password was wrong or the ciphertext was tampered with,
 * SubtleCrypto will throw an OperationError during tag verification.
 */
export async function decryptVaultPayload(
  ciphertextHex: string,
  ivHex: string,
  key: CryptoKey
): Promise<VaultPayload> {
  const ciphertextBytes = hexToBytes(ciphertextHex);
  const ivBytes = hexToBytes(ivHex);

  const decryptedBuffer = await window.crypto.subtle.decrypt(
    {
      name: 'AES-GCM',
      iv: ivBytes as unknown as ArrayBuffer,
      tagLength: 128,
    },
    key,
    ciphertextBytes as unknown as ArrayBuffer
  );

  const decoder = new TextDecoder();
  const jsonString = decoder.decode(decryptedBuffer);
  const parsed = JSON.parse(jsonString) as VaultPayload;

  if (parsed.vaultCheck !== 'SECURE_VAULT_VALID_KEY') {
    throw new Error('Decryption header validation failed');
  }

  return parsed;
}

/**
 * Cryptographically secure random password generator.
 * Uses window.crypto.getRandomValues for uniform character distribution.
 */
export interface PasswordGeneratorOptions {
  length: number;
  includeUppercase: boolean;
  includeLowercase: boolean;
  includeNumbers: boolean;
  includeSymbols: boolean;
  excludeAmbiguous?: boolean;
}

export function generateSecurePassword(options: PasswordGeneratorOptions): string {
  let uppercase = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
  let lowercase = 'abcdefghijkmnopqrstuvwxyz';
  let numbers = '23456789';
  let symbols = '!@#$%^&*()-_=+[]{}<>?';

  if (!options.excludeAmbiguous) {
    uppercase += 'IO';
    lowercase += 'lo';
    numbers += '01';
  }

  let charset = '';
  if (options.includeUppercase) charset += uppercase;
  if (options.includeLowercase) charset += lowercase;
  if (options.includeNumbers) charset += numbers;
  if (options.includeSymbols) charset += symbols;

  if (charset.length === 0) {
    charset = lowercase + numbers;
  }

  const length = Math.max(8, Math.min(64, options.length));
  const randomValues = new Uint32Array(length);
  window.crypto.getRandomValues(randomValues);

  let password = '';
  for (let i = 0; i < length; i++) {
    password += charset[randomValues[i] % charset.length];
  }

  return password;
}

/**
 * Evaluates password strength for feedback.
 */
export function evaluatePasswordStrength(password: string): {
  score: number; // 0 to 4
  label: 'Very Weak' | 'Weak' | 'Fair' | 'Strong' | 'Very Strong';
  feedback: string;
} {
  if (!password) {
    return { score: 0, label: 'Very Weak', feedback: 'Enter a master password' };
  }

  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++;
  if (/\d/.test(password) && /[^A-Za-z0-9]/.test(password)) score++;

  switch (score) {
    case 0:
    case 1:
      return { score: 1, label: 'Weak', feedback: 'Use at least 10 characters with numbers and symbols' };
    case 2:
      return { score: 2, label: 'Fair', feedback: 'Good start. Add more characters for higher security' };
    case 3:
      return { score: 3, label: 'Strong', feedback: 'Strong password meeting safety recommendations' };
    case 4:
    default:
      return { score: 4, label: 'Very Strong', feedback: 'Excellent master password entropy' };
  }
}
