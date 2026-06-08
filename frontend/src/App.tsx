import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, theme } from 'antd';
import { AuthProvider } from '@/store/AuthContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { AppLayout } from '@/components/AppLayout';

import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import BRList from '@/pages/BRList';
import BRCreate from '@/pages/BRCreate';
import BRDetails from '@/pages/BRDetails';
import ProposalUpload from '@/pages/ProposalUpload';
import MatchingAnalysis from '@/pages/MatchingAnalysis';
import ComparisonView from '@/pages/ComparisonView';
import AdminPanel from '@/pages/AdminPanel';

function PrivatePage({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <AppLayout>{children}</AppLayout>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <ConfigProvider theme={{ algorithm: theme.defaultAlgorithm }}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={<PrivatePage><Dashboard /></PrivatePage>} />
            <Route path="/br-projects" element={<PrivatePage><BRList /></PrivatePage>} />
            <Route path="/br-projects/new" element={<PrivatePage><BRCreate /></PrivatePage>} />
            <Route path="/br-projects/:id" element={<PrivatePage><BRDetails /></PrivatePage>} />
            <Route path="/br-projects/:brId/upload-proposal" element={<PrivatePage><ProposalUpload /></PrivatePage>} />
            <Route path="/proposals/:proposalId/analysis" element={<PrivatePage><MatchingAnalysis /></PrivatePage>} />
            <Route path="/comparison" element={<PrivatePage><ComparisonView /></PrivatePage>} />
            <Route path="/admin" element={<PrivatePage><AdminPanel /></PrivatePage>} />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ConfigProvider>
  );
}
