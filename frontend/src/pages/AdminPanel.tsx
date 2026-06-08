import { useEffect, useState } from 'react';
import {
  Row, Col, Card, Table, Tag, Typography, Tabs, Statistic,
  Alert, Spin, Badge,
} from 'antd';
import { adminApi } from '@/api/client';

function HealthTag({ value }: { value: string }) {
  const color = value === 'ok' ? 'success' : value === 'cpu_only' ? 'warning' : 'error';
  return <Badge status={color} text={value} />;
}

export default function AdminPanel() {
  const [feedbackReport, setFeedbackReport] = useState<any>(null);
  const [aiStats, setAiStats] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [auditTotal, setAuditTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      adminApi.feedbackReport().catch(() => null),
      adminApi.aiStats().catch(() => null),
      adminApi.health().catch(() => null),
      adminApi.auditLogs(1),
    ])
      .then(([fr, ai, h, al]) => {
        setFeedbackReport(fr?.data?.data);
        setAiStats(ai?.data?.data);
        setHealth(h?.data?.data);
        setAuditLogs(al.data.data.items ?? []);
        setAuditTotal(al.data.data.total ?? 0);
      })
      .catch(() => setError('Failed to load admin data.'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', marginTop: 80 }} />;
  if (error) return <Alert message={error} type="error" />;

  const auditColumns = [
    { title: 'Action', dataIndex: 'action', key: 'action' },
    { title: 'Resource', dataIndex: 'resource_type', key: 'resource_type' },
    { title: 'Resource ID', dataIndex: 'resource_id', key: 'resource_id', render: (v: string) => v ? v.slice(0, 8) + '…' : '—' },
    { title: 'IP', dataIndex: 'ip_address', key: 'ip', render: (v: string) => v ?? '—' },
    { title: 'Time', dataIndex: 'created_at', key: 'created_at', render: (v: string) => new Date(v).toLocaleString() },
  ];

  return (
    <div>
      <Typography.Title level={4} style={{ marginBottom: 24 }}>Admin Panel</Typography.Title>

      <Tabs
        items={[
          {
            key: 'health',
            label: 'System Health',
            children: health ? (
              <Row gutter={[16, 16]}>
                {Object.entries(health).map(([k, v]) => (
                  <Col key={k} xs={24} sm={12} md={6}>
                    <Card size="small" title={k}>
                      <HealthTag value={String(v)} />
                    </Card>
                  </Col>
                ))}
              </Row>
            ) : <Alert message="Health data not available (requires admin role)" type="warning" />,
          },
          {
            key: 'feedback',
            label: 'Feedback Quality',
            children: feedbackReport ? (
              <Row gutter={[16, 16]}>
                <Col xs={12} md={6}><Card><Statistic title="Total Feedback" value={feedbackReport.total_feedback} /></Card></Col>
                <Col xs={12} md={6}><Card><Statistic title="Marked Useful" value={feedbackReport.useful_feedback} /></Card></Col>
                <Col xs={12} md={6}><Card><Statistic title="Score Corrections" value={feedbackReport.total_corrections} /></Card></Col>
                <Col xs={12} md={6}><Card><Statistic title="Avg Rating" value={feedbackReport.average_rating ?? '—'} suffix="/ 5" /></Card></Col>
              </Row>
            ) : <Alert message="Feedback data not available (requires admin role)" type="warning" />,
          },
          {
            key: 'ai',
            label: 'AI Learning',
            children: aiStats ? (
              <Row gutter={[16, 16]}>
                <Col xs={12} md={6}><Card><Statistic title="Total Corrections" value={aiStats.total_corrections} /></Card></Col>
                <Col xs={12} md={6}><Card><Statistic title="Applied to Model" value={aiStats.applied} /></Card></Col>
                <Col xs={12} md={6}><Card><Statistic title="Pending" value={aiStats.pending} /></Card></Col>
                <Col xs={12} md={6}><Card><Statistic title="Avg Score Delta" value={aiStats.avg_delta ?? '—'} /></Card></Col>
              </Row>
            ) : <Alert message="AI stats not available (requires admin role)" type="warning" />,
          },
          {
            key: 'audit',
            label: `Audit Logs (${auditTotal})`,
            children: (
              <Table
                rowKey="id"
                dataSource={auditLogs}
                columns={auditColumns}
                size="small"
                pagination={{ pageSize: 20, total: auditTotal }}
              />
            ),
          },
        ]}
      />
    </div>
  );
}
