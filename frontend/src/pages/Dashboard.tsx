import { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Typography, Table, Tag, Spin, Alert, Progress } from 'antd';
import {
  ProjectOutlined, FileTextOutlined, CheckCircleOutlined,
  ClockCircleOutlined, TeamOutlined, StarOutlined,
} from '@ant-design/icons';
import { adminApi } from '@/api/client';
import type { DashboardStats, SystemHealth } from '@/types';

const statusColor = (s: string) =>
  ({ ok: 'green', error: 'red', cpu_only: 'orange', unknown: 'default' }[s] ?? 'default');

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const [s, h, a] = await Promise.all([
        adminApi.dashboard(),
        adminApi.health().catch(() => ({ data: { data: null } })),
        adminApi.activities(10),
      ]);
      setStats(s.data.data);
      setHealth(h.data.data);
      setActivities(a.data.data ?? []);
    } catch {
      setError('Failed to load dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); const t = setInterval(load, 30_000); return () => clearInterval(t); }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', marginTop: 80 }} />;
  if (error) return <Alert message={error} type="error" />;

  const cards = [
    { title: 'BR Projects', value: stats?.total_br_projects, icon: <ProjectOutlined />, color: '#1677ff' },
    { title: 'Proposals', value: stats?.total_proposals, icon: <FileTextOutlined />, color: '#52c41a' },
    { title: 'Matched', value: stats?.total_matched, icon: <CheckCircleOutlined />, color: '#13c2c2' },
    { title: 'Pending', value: stats?.pending_processing, icon: <ClockCircleOutlined />, color: '#fa8c16' },
    { title: 'Users', value: stats?.total_users, icon: <TeamOutlined />, color: '#722ed1' },
    { title: 'Feedback', value: stats?.total_feedback, icon: <StarOutlined />, color: '#eb2f96' },
  ];

  return (
    <div>
      <Typography.Title level={4} style={{ marginBottom: 24 }}>Dashboard</Typography.Title>

      <Row gutter={[16, 16]}>
        {cards.map((c) => (
          <Col xs={24} sm={12} lg={4} key={c.title}>
            <Card>
              <Statistic
                title={c.title}
                value={c.value ?? 0}
                prefix={<span style={{ color: c.color }}>{c.icon}</span>}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {stats?.avg_match_score != null && (
          <Col xs={24} md={8}>
            <Card title="Avg Match Score">
              <Progress
                type="dashboard"
                percent={Math.round(stats.avg_match_score * 100)}
                strokeColor={stats.avg_match_score >= 0.7 ? '#52c41a' : '#faad14'}
              />
            </Card>
          </Col>
        )}

        {health && (
          <Col xs={24} md={8}>
            <Card title="System Health">
              {Object.entries(health).map(([k, v]) => (
                <div key={k} style={{ marginBottom: 6 }}>
                  <Tag color={statusColor(v as string)}>{String(v).toUpperCase()}</Tag>
                  <Typography.Text type="secondary"> {k}</Typography.Text>
                </div>
              ))}
            </Card>
          </Col>
        )}

        <Col xs={24} md={health ? 8 : 16}>
          <Card title="Recent Activity">
            <Table
              size="small"
              rowKey="id"
              dataSource={activities}
              pagination={false}
              columns={[
                { title: 'Action', dataIndex: 'action', key: 'action' },
                { title: 'Resource', dataIndex: 'resource_type', key: 'resource_type' },
                {
                  title: 'Time', dataIndex: 'created_at', key: 'created_at',
                  render: (v: string) => new Date(v).toLocaleString(),
                },
              ]}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
