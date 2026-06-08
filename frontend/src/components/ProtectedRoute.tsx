import { Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuth } from '@/store/AuthContext';
import type { ReactNode } from 'react';

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <Spin fullscreen />;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
