import { useState } from 'react';
import {
  Form, Input, Button, Card, DatePicker, InputNumber,
  Typography, Space, message, Upload, Divider,
} from 'antd';
import { UploadOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { UploadFile } from 'antd';
import { brApi } from '@/api/client';

export default function BRCreate() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [createdId, setCreatedId] = useState<string | null>(null);

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      const payload = {
        title: values.title,
        description: values.description,
        deadline: values.deadline?.toISOString(),
        budget_min: values.budget_min,
        budget_max: values.budget_max,
      };
      const res = await brApi.create(payload);
      const id = res.data.data.id;
      setCreatedId(id);

      if (fileList.length > 0 && fileList[0].originFileObj) {
        await brApi.uploadDocument(id, fileList[0].originFileObj as File);
        message.success('BR project created and document uploaded!');
      } else {
        message.success('BR project created!');
      }
      navigate(`/br-projects/${id}`);
    } catch (e: any) {
      message.error(e?.response?.data?.message ?? 'Failed to create BR project');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 720, margin: '0 auto' }}>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/br-projects')}>Back</Button>
        <Typography.Title level={4} style={{ margin: 0 }}>New BR Project</Typography.Title>
      </Space>

      <Card>
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item name="title" label="Project Title" rules={[{ required: true }]}>
            <Input placeholder="e.g. E-Commerce Platform RFP 2024" />
          </Form.Item>

          <Form.Item name="description" label="Description">
            <Input.TextArea rows={4} placeholder="Describe the business requirement..." />
          </Form.Item>

          <Form.Item name="deadline" label="Submission Deadline">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="budget_min" label="Budget Min ($)">
              <InputNumber min={0} style={{ width: 180 }} formatter={(v) => `${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} />
            </Form.Item>
            <Form.Item name="budget_max" label="Budget Max ($)">
              <InputNumber min={0} style={{ width: 180 }} formatter={(v) => `${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} />
            </Form.Item>
          </Space>

          <Divider>Upload BR Document (optional)</Divider>

          <Form.Item label="BR Document (PDF/DOCX)">
            <Upload
              fileList={fileList}
              beforeUpload={(file) => { setFileList([file as any]); return false; }}
              onRemove={() => setFileList([])}
              accept=".pdf,.docx,.doc,.txt"
              maxCount={1}
            >
              <Button icon={<UploadOutlined />}>Select File</Button>
            </Upload>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              Requirements will be automatically extracted from the document.
            </Typography.Text>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                Create BR Project
              </Button>
              <Button onClick={() => navigate('/br-projects')}>Cancel</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
