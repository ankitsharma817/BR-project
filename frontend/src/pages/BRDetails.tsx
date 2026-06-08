import { useEffect, useState } from 'react';
import {
  Tabs, Table, Button, Tag, Space, Typography, Popconfirm, message,
  Card, Descriptions, Modal, Form, Input, Select, Spin, Badge,
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, UploadOutlined,
  ArrowLeftOutlined, FileAddOutlined,
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { brApi, proposalApi } from '@/api/client';
import type { BRProject, Requirement, Proposal } from '@/types';
import { ScoreBadge } from '@/components/ScoreBadge';

const PRIORITY_COLOR: Record<string, string> = {
  critical: 'red', high: 'orange', medium: 'blue', low: 'default',
};
const CATEGORY_COLOR: Record<string, string> = {
  functional: 'cyan', technical: 'purple', compliance: 'gold',
  security: 'red', timeline: 'lime', resource: 'magenta', deliverables: 'geekblue',
};

export default function BRDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [br, setBr] = useState<BRProject | null>(null);
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [reqModal, setReqModal] = useState(false);
  const [editReq, setEditReq] = useState<Requirement | null>(null);
  const [form] = Form.useForm();

  const load = async () => {
    if (!id) return;
    try {
      const [brRes, propRes] = await Promise.all([
        brApi.get(id),
        proposalApi.list(id, 1, 50),
      ]);
      setBr(brRes.data.data);
      setRequirements(brRes.data.data.requirements ?? []);
      setProposals(propRes.data.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [id]);

  const handleDeleteReq = async (reqId: string) => {
    await brApi.deleteRequirement(id!, reqId);
    message.success('Requirement deleted');
    setRequirements((prev) => prev.filter((r) => r.id !== reqId));
  };

  const openReqModal = (req?: Requirement) => {
    setEditReq(req ?? null);
    form.setFieldsValue(req ?? { category: 'functional', priority: 'medium' });
    setReqModal(true);
  };

  const handleReqSubmit = async () => {
    const values = await form.validateFields();
    if (editReq) {
      await brApi.updateRequirement(id!, editReq.id, values);
      message.success('Requirement updated');
    } else {
      await brApi.createRequirement(id!, values);
      message.success('Requirement added');
    }
    setReqModal(false);
    load();
  };

  if (loading) return <Spin size="large" style={{ display: 'block', marginTop: 80 }} />;
  if (!br) return <Typography.Text type="danger">BR project not found.</Typography.Text>;

  const reqColumns = [
    { title: '#', key: 'i', render: (_: any, __: any, i: number) => i + 1, width: 48 },
    { title: 'Requirement', dataIndex: 'text', key: 'text' },
    {
      title: 'Category', dataIndex: 'category', key: 'category',
      render: (c: string) => <Tag color={CATEGORY_COLOR[c] ?? 'default'}>{c}</Tag>,
    },
    {
      title: 'Priority', dataIndex: 'priority', key: 'priority',
      render: (p: string) => <Tag color={PRIORITY_COLOR[p] ?? 'default'}>{p.toUpperCase()}</Tag>,
    },
    { title: 'Source', dataIndex: 'source', key: 'source', render: (s: string) => <Tag>{s}</Tag> },
    {
      title: 'Actions', key: 'actions',
      render: (_: any, r: Requirement) => (
        <Space>
          <Button icon={<EditOutlined />} size="small" onClick={() => openReqModal(r)} />
          <Popconfirm title="Delete requirement?" onConfirm={() => handleDeleteReq(r.id)}>
            <Button icon={<DeleteOutlined />} size="small" danger />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const propColumns = [
    { title: 'Vendor', dataIndex: 'vendor_name', key: 'vendor' },
    {
      title: 'Score', key: 'score',
      render: (_: any, p: Proposal) => <ScoreBadge score={p.overall_score} />,
    },
    {
      title: 'Status', dataIndex: 'status', key: 'status',
      render: (s: string) => (
        <Badge
          status={s === 'matched' ? 'success' : s === 'processing' ? 'processing' : s === 'failed' ? 'error' : 'default'}
          text={s}
        />
      ),
    },
    {
      title: 'Cost', key: 'cost',
      render: (_: any, p: Proposal) =>
        p.proposed_cost ? `$${p.proposed_cost.toLocaleString()}` : '—',
    },
    {
      title: 'Timeline', key: 'timeline',
      render: (_: any, p: Proposal) =>
        p.proposed_timeline_months ? `${p.proposed_timeline_months} months` : '—',
    },
    {
      title: 'Actions', key: 'actions',
      render: (_: any, p: Proposal) => (
        <Space>
          <Button type="link" size="small" onClick={() => navigate(`/proposals/${p.id}/analysis`)}>
            Analysis
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/br-projects')}>Back</Button>
        <Typography.Title level={4} style={{ margin: 0 }}>{br.title}</Typography.Title>
        <Tag color={{ draft: 'default', active: 'blue', closed: 'orange', archived: 'red' }[br.status] ?? 'default'}>
          {br.status.toUpperCase()}
        </Tag>
      </Space>

      <Card style={{ marginBottom: 16 }}>
        <Descriptions size="small" column={{ xs: 1, sm: 2, md: 3 }}>
          {br.description && <Descriptions.Item label="Description" span={3}>{br.description}</Descriptions.Item>}
          {br.deadline && <Descriptions.Item label="Deadline">{new Date(br.deadline).toLocaleDateString()}</Descriptions.Item>}
          {br.budget_min != null && (
            <Descriptions.Item label="Budget">
              ${br.budget_min.toLocaleString()} – ${br.budget_max?.toLocaleString() ?? '?'}
            </Descriptions.Item>
          )}
          <Descriptions.Item label="Requirements">{br.requirement_count}</Descriptions.Item>
          <Descriptions.Item label="Proposals">{br.proposal_count}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Tabs
        items={[
          {
            key: 'requirements',
            label: `Requirements (${requirements.length})`,
            children: (
              <>
                <Space style={{ marginBottom: 12 }}>
                  <Button icon={<PlusOutlined />} onClick={() => openReqModal()}>Add Requirement</Button>
                  <Button
                    icon={<FileAddOutlined />}
                    onClick={() => navigate(`/br-projects/${id}/upload-doc`)}
                  >
                    Upload Document
                  </Button>
                </Space>
                <Table rowKey="id" dataSource={requirements} columns={reqColumns} size="small" />
              </>
            ),
          },
          {
            key: 'proposals',
            label: `Proposals (${proposals.length})`,
            children: (
              <>
                <Space style={{ marginBottom: 12 }}>
                  <Button
                    type="primary" icon={<UploadOutlined />}
                    onClick={() => navigate(`/br-projects/${id}/upload-proposal`)}
                  >
                    Upload Proposal
                  </Button>
                </Space>
                <Table rowKey="id" dataSource={proposals} columns={propColumns} size="small" />
              </>
            ),
          },
        ]}
      />

      <Modal
        title={editReq ? 'Edit Requirement' : 'Add Requirement'}
        open={reqModal}
        onOk={handleReqSubmit}
        onCancel={() => setReqModal(false)}
        okText="Save"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="text" label="Requirement Text" rules={[{ required: true }]}>
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="category" label="Category" rules={[{ required: true }]}>
            <Select options={['functional','technical','compliance','security','timeline','resource','deliverables'].map((v) => ({ value: v, label: v }))} />
          </Form.Item>
          <Form.Item name="priority" label="Priority" rules={[{ required: true }]}>
            <Select options={['critical','high','medium','low'].map((v) => ({ value: v, label: v }))} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
