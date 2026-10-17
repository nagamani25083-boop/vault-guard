# Requirements Document

## 1. Application Overview

### 1.1 Application Name
VaultGuard

### 1.2 Application Description
VaultGuard is a client-side encrypted, web-based personal password manager. It provides secure local credential storage, customizable password generation, category-based credential management, genuine vault security health metrics, encrypted backup export, and an integrated cryptographic inspector. It utilizes a premium dark cybersecurity SaaS interface while guaranteeing zero plaintext persistence and zero external server transmission.

## 2. User & Usage Scenarios

### 2.1 Target Users
- Individuals requiring client-side encrypted, zero-knowledge credential management.
- Users looking for a structured tool to generate cryptographically secure passwords, categorize accounts, and evaluate actual vault security metrics.

### 2.2 Core Usage Scenarios
- **Vault Initialization & Unlocking**: A user registers or unlocks the vault using a master password, deriving cryptographic keys into temporary memory.
- **Dashboard Overview**: The user views genuine security metrics (total items, verified weak/reused counts), recent items, and uses quick-actions to generate or add credentials.
- **Credential Lifecycle Management**: The user adds, edits, categorizes, reveals, copies, and deletes saved account items stored securely in IndexedDB.
- **Password Generation**: The user configures character parameters and copies cryptographically secure randomized passwords.
- **Security & Maintenance**: The user checks actual vault health, configures inactivity auto-lock, exports encrypted backups, wipes vault data, or inspects cryptographic operations via the inspector modal.

## 3. Page Structure & Functional Specifications

### 3.1 Information Architecture
```
VaultGuard
├── Authentication
│   ├── Master Registration Screen
│   └── Master Login / Unlock Screen
└── Main Application Shell (Fixed Desktop Sidebar / Responsive Navigation)
    ├── Dashboard View
    │   ├── Greeting Banner (\"Your digital life, secured.\")
    │   ├── Summary Cards (Total Items, Weak Passwords, Reused Passwords)
    │   ├── Search & Quick Add Password Button
    │   ├── Recent Vault Entries
    │   └── Quick Password Generator Widget
    ├── My Vault View
    │   ├── Search & Category Filter (All, Social, Work, Banking, Shopping)
    │   ├── Password Card Grid / Table List
    │   └── Add / Edit Password Modal
    ├── Password Generator View
    │   ├── Parameter Controls (Length, Uppercase, Lowercase, Numbers, Symbols)
    │   ├── Password Output Display
    │   └── Action Buttons (Generate, Copy, Regenerate)
    ├── Security View
    │   ├── Verified Security Overview
    │   ├── Password Health Breakdown (Weak, Reused, Missing Details)
    │   └── Crypto Inspector / DevTools Modal Trigger
    └── Settings View
        ├── Inactivity Auto-Lock Duration Selector
        ├── Master Password Change
        ├── Export Encrypted Backup
        └── Wipe / Reset Vault Data
```

### 3.2 Visual Theme & Styling Guidelines
- **Theme**: Dark premium cybersecurity SaaS aesthetic.
- **Color Palette**:
  - Primary Background: Deep Navy (`#0B1020`)
  - Card Background: Dark Slate (`#141B2D`)
  - Accent Colors: Purple (`#8B5CF6`) and Electric Blue (`#3B82F6`)
  - Text Colors: Crisp White and Soft Grey
- **Styling Elements**: Subtle purple-blue gradients, rounded card borders, clean modern sans-serif typography, and restrained glow hover states.
- **Layout**: Fixed desktop sidebar, compact top navigation, and responsive mobile menu.

### 3.3 Page & Feature Details

#### 3.3.1 Authentication
- **Registration**: Allows setting a master password; calculates derivation salt and initializes `SecureVaultDB` in IndexedDB.
- **Login**: Validates master credentials, derives session key in memory, and decrypts stored entries.
- **State Retention**: In-memory decryption only; auto-purges upon lock or timeout.

#### 3.3.2 Sidebar Navigation
- **Brand Display**: Displays VaultGuard brand name with shield icon.
- **Navigation Links**: Dashboard, My Vault, Password Generator, Security, Settings, and an explicit Lock Vault trigger.
- **Active State**: Visual indicator with accent highlight for the current active route.

#### 3.3.3 Dashboard View
- **Greeting Banner**: Displays headline \"Your digital life, secured.\"
- **Search Field**: Placeholder \"Search your vault...\" for instant item lookup.
- **Add Password**: Prominent primary button opening the Add Password modal.
- **Summary Cards**: Genuine counts of saved credentials and verified security indicators (weak passwords count, reused passwords count) derived from actual vault entries without synthetic scores.
- **Recent Entries**: Displays recent vault items in card or table format with empty states for initial accounts.
- **Quick Generator Access**: Embedded mini-generator for quick password creation.

#### 3.3.4 My Vault View
- **Category Filter**: Filtering across categories (All, Social, Work, Banking, Shopping).
- **Credential List / Cards**:
  - Item metadata: Service name, website URL, username/email, category icon and label.
  - Password field: Masked by default with explicit show/hide toggle.
  - Quick actions: One-click copy for username and password with visual confirmation.
  - Management: Edit and Delete actions (delete requires confirmation dialog).
- **Add / Edit Password Modal**:
  - Fields: Website/Service Name, Website URL, Username/Email, Password, Category dropdown, and Notes.
  - Features: Show/hide toggle, real-time strength meter, cancel, and save actions.

#### 3.3.5 Password Generator View
- **Length Adjustment**: Slider/input for password length (8 to 64 characters).
- **Character Options**: Toggles for Uppercase (A-Z), Lowercase (a-z), Numbers (0-9), and Symbols (!@#$%^&*).
- **Generation Logic**: Generates random strings using standard browser cryptographic randomness (`crypto.getRandomValues`).
- **Actions**: Instant copy with visual feedback, regenerate button, and clear display.

#### 3.3.6 Security & Crypto Inspector
- **Security Status**: Displays verified audit lists of items with weak or reused passwords based strictly on real stored data.
- **Crypto Inspector / DevTools Modal**: Inspects active cryptographic parameters (algorithm: AES-GCM 256, key derivation: PBKDF2 SHA-256 iterations, salt status, IV generation) for technical transparency.

#### 3.3.7 Settings View
- **Inactivity Auto-Lock**: Dropdown selection (e.g., 5 minutes, 15 minutes, 30 minutes, Never).
- **Master Password Update**: Re-encrypts all vault entries under a newly derived key upon verifying the current master password.
- **Export Encrypted Backup**: Exports vault data as an encrypted JSON backup file.
- **Wipe / Reset Vault**: Permanently clears `SecureVaultDB` and local state after explicit user confirmation.

## 4. Business Rules & Core Logic

### 4.1 Cryptographic & Storage Rules
- **Key Derivation**: Derive encryption keys from the master password using PBKDF2 with SHA-256 and a random salt.
- **Data Encryption**: Encrypt each vault entry using AES-GCM (256-bit) with a unique Initialization Vector (IV) prior to storage.
- **Storage Engine**: Persist encrypted ciphertext records into browser IndexedDB named `SecureVaultDB`.
- **Zero Plaintext Persistence**: Master passwords, derived keys, and unencrypted credentials must never be written to persistent storage (IndexedDB, LocalStorage, or cookies).
- **Zero Server Communication**: All cryptographic, audit, and generation processes run entirely client-side without external network calls.

### 4.2 Security Audit & Metric Rules
- **Verified Audit**: Security metrics must solely reflect actual computed vault health (e.g., passwords matching across multiple accounts, lengths below standard complexity threshold).
- **Memory Lifecycle**: In-memory keys and decrypted records are wiped upon manual lock, inactivity trigger, or page reload.

## 5. Exceptions & Edge Cases

| Scenario | Condition | System Behavior |
| :--- | :--- | :--- |
| Invalid Unlock Attempt | Master password does not match derived hash/test block | Reject unlock, show error message, keep encrypted records locked |
| Empty Character Selection | User deselects all character sets in generator | Enforce at least one active character set automatically |
| Vault Wipe Action | User clicks wipe / reset vault | Require explicit confirmation before deleting IndexedDB data and resetting state |
| Inactivity Timeout | Vault remains inactive beyond configured duration | Purge in-memory decrypted keys and redirect to unlock screen |
| Backup Export | User requests backup while vault is unlocked | Generate encrypted JSON payload without exposing plaintext keys |

## 6. Acceptance Criteria

1. The interface adopts the dark premium palette (Deep navy `#0B1020`, Dark slate `#141B2D`, Purple `#8B5CF6`, Electric blue `#3B82F6`) across desktop and mobile navigation.
2. Users can register a master password, initialize `SecureVaultDB`, and unlock the vault into memory.
3. The dashboard displays the greeting banner, search bar, summary cards with genuine security metrics, recent entries, and quick generator access.
4. Users can add, edit, categorize, reveal, copy, and delete credential entries in My Vault.
5. The password generator produces cryptographically secure strings according to configured parameters and provides copy and regenerate controls.
6. The Security view displays genuine audit metrics (weak/reused passwords) and opens the Crypto Inspector modal displaying active cryptographic parameters.
7. Settings allow configuring auto-lock durations, exporting encrypted backup files, and wiping vault data with confirmation.
8. Manual vault lock or inactivity expiration clears decrypted data and in-memory keys, returning to the unlock screen.