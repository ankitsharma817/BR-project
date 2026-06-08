import { useEffect, useState } from 'react';
import {
  Row, Col, Card, Progress, Typography, Table, Tag, Collapse,
  Button, Space, Alert, Spin, Modal, Form, InputNumber, Select, Rate, Input, message,
} from 'antd';
import {
  ReloadOutlined, ExportOutlined, ArrowLeftOutlined, MessageOutlined,
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { matchingApi, feedbackApi } from '@/api/client';
import type { MatchingResult, MatchAnalysis, RequirementMatching } from '@/types';

const LABEL_COLOR: Record<string, string> = {
  strong_match: '#52c41a', partial_match: '#faad14',
  gap_identified: '#fa8c16', missing: '#f5222d',
};
const LABEL_TEXT: Record<string, string> = {
  strong_match: '✅ Strong Match', partial_match: '⚠️ Partial Match',
  gap_identified: '🔶 Gap Identified', missing: '❌ Missing',
};
const RISK_COLOR: Record<string, string> = { high: 'red', medium: 'orange', low: 'green' };
const PRIO_COLOR: Record<string, string> = { HIGH: 'red', MEDIUM: 'orange', LOW: 'green' };

function ScoreCircle({ label, value }: { label: string; value?: number | null }) {
  if (value == null) return null;
  const pct = Math.round(value * 100);
  const color = value >= 0.8 ? '#52c41a' : value >= 0.6 ? '#faad14' : '#f5222d';
  return (
    <Col xs={12} sm={8} md={6} lg={4} style={{ textAlign: 'center', marginBottom: 16 }}>
      <Progress type="circle" percent={pct} strokeColor={color} width={80} />
      <Typography.Text style={{ display: 'block', marginTop: 4, fontSize: 12 }}>{label}</Typography.Text>
    </Col>
  );
}

export default function MatchingAnalysis() {
  const { proposalId } = useParams<{ proposalId: string }>();
  const navigate = useNavigate();
  const [result, setResult] = useState<MatchingResult | null>(null);
  const [analysis, setAnalysis] = useState<MatchAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [recalcLoading, setRecalcLoading] = useState(false);
  const [feedbackModal, setFeedbackModal] = useState(false);
  const [feedbackForm] = Form.useForm();
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [rRes, aRes] = await Promise.all([
        matchingApi.getResult(proposalId!),
        matchingApi.getAnalysis(proposalId!).catch(() => ({ data: { data: null } })),
      ]);
      setResult(rRes.data.data);
      setAnalysis(aRes.data.data);
    } catch (e: any) {
      setError(e?.response?.data?.message ?? 'Matching results not available yet.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [proposalId]);

  const handleRecalculate = async () => {
    setRecalcLoading(true);
    try {
      await matchingApi.recalculate(proposalId!);
      message.info('Recalculation started. Refreshing in 5 seconds...');
      setTimeout(load, 5000);
    } finally {
      setRecalcLoading(false);
    }
  };

  const handleFeedback = async () => {
    const values = await feedbackForm.validateFields();
    await feedbackApi.submit(proposalId!, {
      feedback_type: 'general',
      rating: values.rating,
      comment: values.comment,
      corrected_score: values.corrected_score ? values.corrected_score / 100 : undefined,
      original_score: result?.overall_score,
    });
    message.success('Feedback submitted. Thank you!');
    setFeedbackModal(false);
    feedbackForm.resetFields();
  };

  if (loading) return <Spin size="large" style={{ display: 'block', marginTop: 80 }} />;
  if (error) return (
    <Alert
      message="Results not ready"
      description={error}
      type="warning"
      action={<Button onClick={load}>Retry</Button>}
    />
  );
  if (!result) return null;

  const overallPct = Math.round(result.overall_score * 100);
  const overallColor = result.overall_score >= 0.8 ? '#52c41a' : result.overall_score >= 0.6 ? '#faad14' : '#f5222d';

  const reqColumns = [
    {
      title: 'Requirement', dataIndex: 'br_requirement_text', key: 'br',
      render: (t: string) => <Typography.Text style={{ fontSize: 13 }}>{t}</Typography.Text>,
    },
    {
      title: 'Category', dataIndex: 'br_requirement_category', key: 'cat',
      render: (c: string) => <Tag>{c}</Tag>, width: 120,
    },
    {
      title: 'Priority', dataIndex: 'br_requirement_priority', key: 'prio',
      render: (p: string) => <Tag color={{ critical: 'red', high: 'orange', medium: 'blue', low: 'default' }[p] ?? 'default'}>{p}</Tag>,
      width: 90,
    },
    {
      title: 'Score', dataIndex: 'score', key: 'score', width: 80,
      render: (s: number) => <Typography.Text strong style={{ color: LABEL_COLOR[s >= 0.8 ? 'strong_match' : s >= 0.6 ? 'partial_match' : s >= 0.3 ? 'gap_identified' : 'missing'] }}>{Math.round(s * 100)}%</Typography.Text>,
    },
    {
      title: 'Status', dataIndex: 'label', key: 'label', width: 150,
      render: (l: string) => <Tag color={LABEL_COLOR[l]}>{LABEL_TEXT[l] ?? l}</Tag>,
    },
    {
      title: 'Explanation', dataIndex: 'explanation', key: 'exp',
      render: (e: string) => <Typography.Text type="secondary" style={{ fontSize: 12 }}>{e}</Typography.Text>,
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>Back</Button>
        <Typography.Title level={4} style={{ margin: 0 }}>Matching Analysis</Typography.Title>
      </Space>

      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ReloadOutlined />} loading={recalcLoading} onClick={handleRecalculate}>
          Recalculate
        </Button>
        <Button icon={<MessageOutlined />} onClick={() => setFeedbackModal(true)}>
          Give Feedback
        </Button>
        <Typography.Text type="secondary">Version {result.version} · {new Date(result.calculated_at).toLocaleString()}</Typography.Text>
      </Space>

      {/* Overall Score */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} md={6} style={{ textAlign: 'center' }}>
          <Card>
            <Progress type="dashboard" percent={overallPct} strokeColor={overallColor} width={140} />
            <Typography.Title level={4} style={{ marginTop: 8 }}>Overall Score</Typography.Title>
            {result.executive_summary && (
              <Typography.Paragraph type="secondary" style={{ fontSize: 12, marginTop: 8 }}>
                {result.executive_summary}
              </Typography.Paragraph>
            )}
          </Card>
        </Col>
        <Col xs={24} md={18}>
          <Card title="Category Scores">
            <Row>
              <ScoreCircle label="Functional" value={result.functional_score} />
              <ScoreCircle label="Technical" value={result.technical_score} />
              <ScoreCircle label="Compliance" value={result.compliance_score} />
              <ScoreCircle label="Security" value={result.security_score} />
              <ScoreCircle label="Timeline" value={result.timeline_score} />
              <ScoreCircle label="Resource" value={result.resource_score} />
              <ScoreCircle label="Deliverables" value={result.deliverables_score} />
            </Row>
          </Card>
        </Col>
      </Row>

      {/* Analysis */}
      {analysis && (
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          {analysis.strengths.length > 0 && (
            <Col xs={24} md={12}>
              <Card title="✅ Strengths" size="small">
                {analysis.strengths.map((s, i) => (
                  <Tag key={i} color="green" style={{ marginBottom: 4 }}>{s}</Tag>
                ))}
              </Card>
            </Col>
          )}
          {analysis.gaps.length > 0 && (
            <Col xs={24} md={12}>
              <Card title="❌ Gaps" size="small">
                {analysis.gaps.map((g, i) => (
                  <div key={i} style={{ fontSize: 12, marginBottom: 4, color: '#f5222d' }}>• {g}</div>
                ))}
              </Card>
            </Col>
          )}
          {analysis.risks.length > 0 && (
            <Col xs={24} md={12}>
              <Card title="⚠️ Risks" size="small">
                {analysis.risks.map((r, i) => (
                  <div key={i} style={{ marginBottom: 6 }}>
                    <Tag color={RISK_COLOR[r.level]}>{r.level.toUpperCase()}</Tag>
                    <Typography.Text style={{ fontSize: 12 }}>{r.description}</Typography.Text>
                  </div>
                ))}
              </Card>
            </Col>
          )}
          {analysis.recommendations.length > 0 && (
            <Col xs={24} md={12}>
              <Card title="💡 Recommendations" size="small">
                {analysis.recommendations.map((r, i) => (
                  <div key={i} style={{ marginBottom: 6 }}>
                    <Tag color={PRIO_COLOR[r.priority]}>{r.priority}</Tag>
                    <Typography.Text style={{ fontSize: 12 }}>{r.action}</Typography.Text>
                  </div>
                ))}
              </Card>
            </Col>
          )}
        </Row>
      )}

      {/* Requirement-by-requirement breakdown */}
      <Card title={`Requirement Breakdown (${result.requirement_matchings.length})`}>
        <Table
          rowKey="id"
          dataSource={result.requirement_matchings}
          columns={reqColumns}
          size="small"
          rowClassName={(r: RequirementMatching) =>
            r.label === 'missing' ? 'row-missing' : ''
          }
          pagination={{ pageSize: 20 }}
        />
      </Card>

      {/* Feedback Modal */}
      <Modal
        title="Give Feedback on This Analysis"
        open={feedbackModal}
        onOk={handleFeedback}
        onCancel={() => setFeedbackModal(false)}
        okText="Submit Feedback"
      >
        <Form form={feedbackForm} layout="vertical">
          <Form.Item name="rating" label="Overall Rating">
            <Rate />
          </Form.Item>
          <Form.Item name="comment" label="Comments">
            <Input.TextArea rows={3} placeholder="How accurate was this analysis?" />
          </Form.Item>
          <Form.Item name="corrected_score" label={`Score Correction (current: ${overallPct}%)`}>
            <InputNumber min={0} max={100} addonAfter="%" style={{ width: 160 }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
