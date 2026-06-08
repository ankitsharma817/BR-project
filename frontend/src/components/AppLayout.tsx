import { ReactNode } from 'react';
import { Layout, Menu, Avatar, Dropdown, Typography, Space } from 'antd';
import {
  DashboardOutlined, ProjectOutlined, FileTextOutlined,
  BarChartOutlined, SettingOutlined, LogoutOutlined, UserOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/store/AuthContext';

const { Header, Sider, Content } = Layout;

const NAV = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/br-projects', icon: <ProjectOutlined />, label: 'BR Projects' },
  { key: '/comparison', icon: <BarChartOutlined />, label: 'Compare' },
  { key: '/admin', icon: <SettingOutlined />, label: 'Admin' },
];

export function AppLayout({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const userMenu = {
    items: [
      { key: 'profile', icon: <UserOutlined />, label: 'Profile' },
      { key: 'logout', icon: <LogoutOutlined />, label: 'Logout', danger: true },
    ],
    onClick: async ({ key }: { key: string }) => {
      if (key === 'logout') { await logout(); navigate('/login'); }
    },
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={220} theme="dark" style={{ position: 'fixed', height: '100vh', zIndex: 100 }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #1f3a5e' }}>
          <Typography.Text strong style={{ color: '#fff', fontSize: 16 }}>
            🔍 BR Match
          </Typography.Text>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname.split('/').slice(0, 2).join('/') || '/dashboard']}
          items={NAV}
          onClick={({ key }) => navigate(key)}
          style={{ marginTop: 8 }}
        />
      </Sider>

      <Layout style={{ marginLeft: 220 }}>
        <Header style={{
          background: '#fff', padding: '0 24px', display: 'flex',
          alignItems: 'center', justifyContent: 'flex-end',
          boxShadow: '0 1px 4px rgba(0,0,0,.08)', position: 'sticky', top: 0, zIndex: 99,
        }}>
          <Dropdown menu={userMenu} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar style={{ background: '#1677ff' }} icon={<UserOutlined />} />
              <Typography.Text>{user?.full_name ?? 'User'}</Typography.Text>
            </Space>
          </Dropdown>
        </Header>
        <Content style={{ padding: 24, background: '#f0f2f5', minHeight: 'calc(100vh - 64px)' }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  );
}
