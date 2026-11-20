import type { RobotStatus } from '../../types/robot';

const LABELS: Record<RobotStatus, string> = {
  READY: 'READY',
  RUNNING: 'RUNNING',
  STOPPED: 'STOPPED',
  ERROR: 'ERROR',
};

export default function StatusBadge({ status }: { status: RobotStatus }) {
  const cls =
    status === 'READY'
      ? 'ready'
      : status === 'RUNNING'
        ? 'running'
        : status === 'STOPPED'
          ? 'stopped'
          : 'error';
  return (
    <span className={`badge ${cls}`} title={`Robot status: ${LABELS[status]}`}>
      <span className="dot" />
      {LABELS[status]}
    </span>
  );
}
