import { Tag, Progress } from 'antd';

interface Props {
  score?: number | null;
  showBar?: boolean;
}

function scoreColor(s: number): string {
  if (s >= 0.8) return '#52c41a';
  if (s >= 0.6) return '#faad14';
  if (s >= 0.3) return '#fa8c16';
  return '#f5222d';
}

function scoreLabel(s: number): string {
  if (s >= 0.8) return 'Strong Match';
  if (s >= 0.6) return 'Partial Match';
  if (s >= 0.3) return 'Gap Identified';
  return 'Missing';
}

export function ScoreBadge({ score, showBar = false }: Props) {
  if (score == null) return <Tag color="default">Pending</Tag>;
  const pct = Math.round(score * 100);
  const color = scoreColor(score);
  if (showBar) {
    return (
      <Progress
        percent={pct}
        size="small"
        strokeColor={color}
        format={(p) => `${p}%`}
      />
    );
  }
  return (
    <Tag color={color} style={{ fontWeight: 600 }}>
      {pct}% — {scoreLabel(score)}
    </Tag>
  );
}
