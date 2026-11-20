import { useMemo } from 'react';

import { simStop } from '../../services/api';
import { useRobotStore } from '../../store/robotStore';
import { useSimulationStore } from '../../store/simulationStore';
import StatusBadge from '../StatusBadge/StatusBadge';
import './Header.css';

export default function Header() {
  const info = useRobotStore((s) => s.info);
  const robotStatus = useRobotStore((s) => s.status);
  const setRobotStatus = useRobotStore((s) => s.setStatus);
  const simStatus = useSimulationStore((s) => s.simStatus);
  const wsConnected = useSimulationStore((s) => s.wsConnected);
  const trajectory = useSimulationStore((s) => s.trajectory);

  const status = useMemo(() => {
    if (robotStatus === 'ERROR') return 'ERROR' as const;
    if (simStatus === 'running') return 'RUNNING' as const;
    if (simStatus === 'stopped') return 'STOPPED' as const;
    return 'READY' as const;
  }, [robotStatus, simStatus]);

  const onStop = async () => {
    try {
      await simStop();
      setRobotStatus('STOPPED', null);
    } catch {
      /* status already reflected via WebSocket */
    }
  };

  return (
    <header className="header">
      <div className="header-title">
        {info?.name ?? 'APE SV2-6045'}
        <span className="header-model">
          {info ? `· ${info.official_specs.model}` : ''}
        </span>
      </div>

      <div className="header-right">
        <span
          className={`ws-pill${wsConnected ? ' on' : ''}`}
          title={wsConnected ? 'Simulation stream connected' : 'Simulation stream disconnected'}
        >
          <span className="dot" />
          {wsConnected ? 'WS LINK' : 'WS OFFLINE'}
        </span>

        <StatusBadge status={status} />

        <button
          className="btn danger sm"
          onClick={onStop}
          disabled={simStatus !== 'running' && simStatus !== 'paused' && !trajectory}
          title="Stop the simulation (animation + stream). This is a simulation stop, not a hardware emergency stop."
        >
          ■ STOP
        </button>
      </div>
    </header>
  );
}
