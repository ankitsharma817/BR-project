import { useEffect, useState } from 'react';
import {
  Row, Col, Card, Select, Button, Table, Typography, Tag, Progress,
  Space, Alert, Spin, Empty,
} from 'antd';
import { PlusOutlined, TrophyOutlined } from '@ant-design/icons';
import { matchingApi, brApi } from '@/api/client';
import type { Proposal } from '@/types';
import { proposalApi } from '@/api/client';

const CATS = ['functional', 'technical', 'compliance', 'security', 'timeline', 'resource', 'deliverables'];
const CAT_KEYS: Record<string, string> = {
  functional: 'functional_score', technical: 'technical_score',
  compliance: 'compliance_score', security: 'security_score',
  timeline: 'timeline_score', resource: 'resource_score', deliverables: 'deliverables_score',
};

function scoreColor(s: number | null | undefined): string {
  if (s == null) return '#d9d9d9';
  if (s >= 0.8) return '#52c41a';
  if (s >= 0.6) return '#faad14';
  if (s >= 0.3) return '#fa8c16';
  return '#f5222d';
}

export default function ComparisonView() {
  const [brList, setBrList] = useState<any[]>([]);
  const [selectedBr, setSelectedBr] = useState<string | null>(null);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [comparison, setComparison] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    brApi.list(1, 100).then((r) => setBrList(r.data.items));
  }, []);

  const loadProposals = async (brId: string) => {
    const res = await proposalApi.list(brId, 1, 100, 'matched');
    setProposals(res.data.items);
    setSelectedIds([]);
    setComparison([]);
  };

  const handleCompare = async () => {
    if (selectedIds.length < 2) return;
    setLoading(true);
    setError(null);
    try {
      const res = await matchingApi.compare(selectedIds);
      setComparison(res.data.data);
    } catch {
      setError('Failed to load comparison data.');
    } finally {
      setLoading(false);
    }
  };

  const winner = comparison.length > 0 ? comparison[0] : null;

  const columns = [
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (c: string) => <Tag>{c}</Tag>,
      fixed: 'left' as const,
      width: 130,
    },
    ...comparison.map((c) => ({
      title: (
        <Space direction="vertical" size={2} style={{ textAlign: 'center' }}>
          {winner?.vendor_name === c.vendor_name && <TrophyOutlined style={{ color: '#faad14' }} />}
          <Typography.Text strong>{c.vendor_name}</Typography.Text>
          <Typography.Text type="secondary" style={{ fontSize: 11 }}>
            Overall: {c.overall_score != null ? `${Math.round(c.overall_score * 100)}%` : 'N/A'}
          </Typography.Text>
        </Space>
      ),
      key: c.proposal_id,
      align: 'center' as const,
      render: (_: any, row: any) => {
        const score = c.category_scores?.[row.category];
        return (
          <Progress
            percent={score != null ? Math.round(score * 100) : 0}
            size="small"
            strokeColor={scoreColor(score)}
            style={{ width: 100 }}
          />
        );
      },
    })),
  ];

  const tableData = CATS.map((c) => ({ category: c, key: c }));

  return (
    <div>
      <Typography.Title level={4} style={{ marginBottom: 24 }}>Proposal Comparison</Typography.Title>

      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Select
            placeholder="Select BR Project"
            style={{ width: 300 }}
            options={brList.map((b) => ({ value: b.id, label: b.title }))}
            onChange={(v) => { setSelectedBr(v); loadProposals(v); }}
          />
          {proposals.length > 0 && (
            <Select
              mode="multiple"
              placeholder="Select proposals to compare (2–4)"
              style={{ width: 400 }}
              value={selectedIds}
              onChange={setSelectedIds}
              options={proposals.map((p) => ({
                value: p.id,
                label: `${p.vendor_name} (${p.overall_score != null ? Math.round(p.overall_score * 100) + '%' : 'pending'})`,
              }))}
              maxTagCount={4}
            />
          )}
          <Button
            type="primary"
            onClick={handleCompare}
            disabled={selectedIds.length < 2}
          >
            Compare
          </Button>
        </Space>
      </Card>

      {error && <Alert message={error} type="error" style={{ marginBottom: 16 }} />}
      {loading && <Spin />}

      {comparison.length > 0 && (
        <>
          {winner && (
            <Alert
              type="success"
              icon={<TrophyOutlined />}
              message={
                <Typography.Text>
                  Best match: <Typography.Text strong>{winner.vendor_name}</Typography.Text> with{' '}
                  <Typography.Text strong>
                    {Math.round(winner.overall_score * 100)}%
                  </Typography.Text> overall score
                </Typography.Text>
              }
              style={{ marginBottom: 16 }}
              showIcon
            />
          )}

          {/* Overall score bar chart */}
          <Card title="Overall Score Comparison" style={{ marginBottom: 16 }}>
            <Row gutter={[16, 16]}>
              {comparison.map((c) => (
                <Col key={c.proposal_id} xs={24} sm={12} md={6}>
                  <Card size="small" style={{ textAlign: 'center' }}>
                    {winner?.vendor_name === c.vendor_name && (
                      <TrophyOutlined style={{ color: '#faad14', fontSize: 20, display: 'block', marginBottom: 4 }} />
                    )}
                    <Typography.Text strong>{c.vendor_name}</Typography.Text>
                    <Progress
                      type="circle"
                      percent={c.overall_score != null ? Math.round(c.overall_score * 100) : 0}
                      strokeColor={scoreColor(c.overall_score)}
                      width={100}
                      style={{ display: 'block', margin: '12px auto 0' }}
                    />
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>

          <Card title="Category-by-Category Breakdown">
            <Table
              dataSource={tableData}
              columns={columns}
              pagination={false}
              size="small"
              scroll={{ x: true }}
            />
          </Card>
        </>
      )}

      {!loading && comparison.length === 0 && selectedBr && (
        <Empty description="Select 2 or more matched proposals and click Compare" />
      )}
    </div>
  );
}
