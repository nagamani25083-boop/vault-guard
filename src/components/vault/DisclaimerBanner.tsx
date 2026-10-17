import React from 'react';
import { AlertTriangle, ShieldCheck, Database, HardDriveDownload } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface DisclaimerBannerProps {
  compact?: boolean;
}

export const DisclaimerBanner: React.FC<DisclaimerBannerProps> = ({ compact = false }) => {
  if (compact) {
    return (
      <div className="bg-muted/70 border border-border px-3 py-2 text-xs text-muted-foreground flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 truncate">
          <AlertTriangle className="h-3.5 w-3.5 text-primary shrink-0" />
          <span className="truncate">
            <strong>B.Tech CSE Project Prototype:</strong> Local-only storage. Not audited for real secrets.
          </span>
        </div>
        <Badge variant="outline" className="text-[10px] shrink-0 font-normal">
          Fake Accounts Only
        </Badge>
      </div>
    );
  }

  return (
    <div className="border border-border bg-card p-4 text-sm text-foreground">
      <div className="flex items-start gap-3">
        <div className="p-2 border border-border bg-muted/50 shrink-0">
          <ShieldCheck className="h-5 w-5 text-foreground" />
        </div>
        <div className="flex-1 min-w-0 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <h4 className="font-semibold text-foreground text-sm">
              Academic Security Notice & Prototype Disclaimer
            </h4>
            <Badge variant="outline" className="text-xs font-mono">
              v1.0-prototype
            </Badge>
          </div>
          <p className="text-muted-foreground text-xs leading-relaxed">
            <strong>SecureVault</strong> is an educational prototype built for a 1st-year B.Tech CSE project.
            All encryption uses the standard <strong>browser Web Crypto API (PBKDF2 + AES-256-GCM)</strong> and
            saves encrypted records exclusively into your browser&apos;s <strong>IndexedDB</strong>.
            This project <strong>has not undergone a professional commercial security audit</strong>.
            Please use <strong>fake test credentials only</strong>. Never enter real banking or primary personal passwords.
          </p>
          <div className="flex flex-wrap items-center gap-3 pt-1 text-[11px] text-muted-foreground">
            <span className="flex items-center gap-1">
              <Database className="h-3 w-3" /> Zero Server Telemetry
            </span>
            <span className="flex items-center gap-1">
              <HardDriveDownload className="h-3 w-3" /> 100% Local Browser Execution
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
