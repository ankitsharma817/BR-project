import { useState } from 'react';
import {
  Form, Input, InputNumber, Button, Card, Upload, Typography,
  Space, message, Steps, Result, Progress,
} from 'antd';
import { InboxOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import type { UploadFile } from 'antd';
import { proposalApi } from '@/api/client';

const { Dragger } = Upload;

export default function ProposalUpload() {
  const { brId } = useParams<{ brId: string }>();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [done, setDone] = useState<{ id: string; vendor: string } | null>(null);

  const onFinish = async (values: any) => {
    if (!file) { message.error('Please select a proposal file'); return; }
    setUploading(true);
    setProgress(20);
    try {
      const res = await proposalApi.upload(brId!, file, {
        vendor_name: values.vendor_name,
        vendor_contact: values.vendor_contact,
        vendor_email: values.vendor_email,
        proposed_cost: values.proposed_cost,
        proposed_timeline_months: values.proposed_timeline_months,
      });
      setProgress(100);
      setDone({ id: res.data.data.id, vendor: values.vendor_name });
      message.success('Proposal uploaded! Matching is running in background.');
    } catch (e: any) {
      message.error(e?.response?.data?.message ?? 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  if (done) {
    return (
      <div style={{ maxWidth: 600, margin: '40px auto' }}>
        <Result
          status="success"
          title={`${done.vendor}'s proposal uploaded!`}
          subTitle="AI matching is running in the background. Check back in a minute for results."
          extra={[
            <Button type="primary" key="analysis" onClick={() => navigate(`/proposals/${done.id}/analysis`)}>
              View Analysis
            </Button>,
            <Button key="back" onClick={() => navigate(`/br-projects/${brId}`)}>
              Back to BR Project
            </Button>,
          ]}
        />
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 720, margin: '0 auto' }}>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(`/br-projects/${brId}`)}>Back</Button>
        <Typography.Title level={4} style={{ margin: 0 }}>Upload Vendor Proposal</Typography.Title>
      </Space>

      <Steps
        size="small"
        current={0}
        style={{ marginBottom: 24 }}
        items={[
          { title: 'Upload' },
          { title: 'AI Extraction' },
          { title: 'Matching' },
          { title: 'Results' },
        ]}
      />

      <Card>
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Typography.Title level={5}>Vendor Information</Typography.Title>

          <Form.Item name="vendor_name" label="Vendor Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. Acme Corp" />
          </Form.Item>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="vendor_contact" label="Contact Person" style={{ flex: 1 }}>
              <Input placeholder="John Smith" />
            </Form.Item>
            <Form.Item name="vendor_email" label="Contact Email" style={{ flex: 1 }}>
              <Input type="email" placeholder="john@acme.com" />
            </Form.Item>
          </Space>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="proposed_cost" label="Proposed Cost ($)" style={{ flex: 1 }}>
              <InputNumber
                min={0} style={{ width: '100%' }}
                formatter={(v) => `${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              />
            </Form.Item>
            <Form.Item name="proposed_timeline_months" label="Timeline (months)" style={{ flex: 1 }}>
              <InputNumber min={1} max={120} style={{ width: '100%' }} />
            </Form.Item>
          </Space>

          <Typography.Title level={5}>Proposal Document</Typography.Title>

          <Form.Item>
            <Dragger
              beforeUpload={(f) => { setFile(f); return false; }}
              onRemove={() => setFile(null)}
              accept=".pdf,.docx,.doc,.txt"
              maxCount={1}
              fileList={file ? [{ uid: '1', name: file.name, status: 'done' } as UploadFile] : []}
            >
              <p className="ant-upload-drag-icon"><InboxOutlined /></p>
              <p className="ant-upload-text">Click or drag proposal file here</p>
              <p className="ant-upload-hint">Supports PDF, DOCX, DOC, TXT — max 50MB</p>
            </Dragger>
          </Form.Item>

          {uploading && <Progress percent={progress} style={{ marginBottom: 16 }} />}

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={uploading}>
                Upload & Start Matching
              </Button>
              <Button onClick={() => navigate(`/br-projects/${brId}`)}>Cancel</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
