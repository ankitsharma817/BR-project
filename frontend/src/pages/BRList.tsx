import { useEffect, useState } from 'react';
import {
  Table, Button, Tag, Space, Typography, Popconfirm,
  message, Input, Select, Card, Tooltip,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, SearchOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { brApi } from '@/api/client';
import type { BRProject } from '@/types';

const STATUS_COLOR: Record<string, string> = {
  draft: 'default', active: 'blue', closed: 'orange', archived: 'red',
};

export default function BRList() {
  const navigate = useNavigate();
  const [data, setData] = useState<BRProject[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<string | undefined>();
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);

  const load = async (p = page, s = status) => {
    setLoading(true);
    try {
      const res = await brApi.list(p, 10, s);
      setData(res.data.items);
      setTotal(res.data.total);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [page, status]);

  const handleDelete = async (id: string) => {
    try {
      await brApi.delete(id);
      message.success('BR project deleted');
      load();
    } catch {
      message.error('Failed to delete');
    }
  };

  const filtered = search
    ? data.filter((d) => d.title.toLowerCase().includes(search.toLowerCase()))
    : data;

  const columns = [
    {
      title: 'Title', dataIndex: 'title', key: 'title',
      render: (t: string, r: BRProject) => (
        <Button type="link" onClick={() => navigate(`/br-projects/${r.id}`)}>{t}</Button>
      ),
    },
    {
      title: 'Status', dataIndex: 'status', key: 'status',
      render: (s: string) => <Tag color={STATUS_COLOR[s] ?? 'default'}>{s.toUpperCase()}</Tag>,
    },
    { title: 'Requirements', dataIndex: 'requirement_count', key: 'req', align: 'center' as const },
    { title: 'Proposals', dataIndex: 'proposal_count', key: 'prop', align: 'center' as const },
    {
      title: 'Deadline', dataIndex: 'deadline', key: 'deadline',
      render: (d: string | null) => d ? new Date(d).toLocaleDateString() : '—',
    },
    {
      title: 'Budget', key: 'budget',
      render: (_: any, r: BRProject) =>
        r.budget_min != null
          ? `$${r.budget_min.toLocaleString()} – $${r.budget_max?.toLocaleString() ?? '?'}`
          : '—',
    },
    {
      title: 'Actions', key: 'actions',
      render: (_: any, r: BRProject) => (
        <Space>
          <Tooltip title="View">
            <Button icon={<EyeOutlined />} size="small" onClick={() => navigate(`/br-projects/${r.id}`)} />
          </Tooltip>
          <Tooltip title="Edit">
            <Button icon={<EditOutlined />} size="small" onClick={() => navigate(`/br-projects/${r.id}/edit`)} />
          </Tooltip>
          <Popconfirm title="Delete this BR project?" onConfirm={() => handleDelete(r.id)}>
            <Tooltip title="Delete">
              <Button icon={<DeleteOutlined />} size="small" danger />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>BR Projects</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/br-projects/new')}>
          New BR Project
        </Button>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Space>
          <Input
            placeholder="Search by title..."
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 240 }}
          />
          <Select
            placeholder="Filter by status"
            allowClear
            style={{ width: 160 }}
            onChange={(v) => { setStatus(v); setPage(1); }}
            options={[
              { value: 'draft', label: 'Draft' },
              { value: 'active', label: 'Active' },
              { value: 'closed', label: 'Closed' },
              { value: 'archived', label: 'Archived' },
            ]}
          />
        </Space>
      </Card>

      <Table
        rowKey="id"
        dataSource={filtered}
        columns={columns}
        loading={loading}
        pagination={{
          current: page, total, pageSize: 10,
          onChange: (p) => setPage(p),
          showTotal: (t) => `${t} projects`,
        }}
      />
    </div>
  );
}
