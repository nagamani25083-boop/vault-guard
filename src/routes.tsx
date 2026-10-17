import { VaultPage } from './pages/VaultPage';
import type { ReactNode } from 'react';

export interface RouteConfig {
  name: string;
  path: string;
  element: ReactNode;
  visible?: boolean;
  public?: boolean;
}

export const routes: RouteConfig[] = [
  {
    name: 'SecureVault',
    path: '/',
    element: <VaultPage />,
    public: true,
  },
];
