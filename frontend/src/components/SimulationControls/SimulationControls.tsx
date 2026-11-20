import { simPause, simResume, simStart, simStop } from '../../services/api';
import { getSimulationSocket } from '../../hooks/useSimulationSocket';
import { useRobotStore } from '../../store/robotStore';
import { useSimulationStore } from '../../store/simulationStore';

/**
 * Playback controls shared by every page that plays a trajectory.
 * Commands go through the WebSocket when connected, REST otherwise.
 */
export default function SimulationControls({ withRestart = true }: { withRestart?: boolean }) {
  const trajectory = useSimulationStore((s) => s.trajectory);
  const simStatus = useSimulationStore((s) => s.simStatus);
  const simTime = useSimulationStore((s) => s.simTime);
  const progress = useSimulationStore((s) => s.progress);
  const setSimStatus = useSimulationStore((s) => s.setSimStatus);
  const setStatus = useRobotStore((s) => s.setStatus);

  const duration = trajectory?.duration ?? 0;

  const play = async () => {
    if (!trajectory) return;
    setStatus('RUNNING');
    setSimStatus('running');
    const sock = getSimulationSocket();
    if (sock) sock.start(trajectory.trajectory_id, 1);
    else await simStart(trajectory.trajectory_id, 1);
  };

  const pause = async () => {
    setSimStatus('paused');
    const sock = getSimulationSocket();
    if (sock) sock.pause();
    else await simPause();
  };

  const resume = async () => {
    setSimStatus('running');
    const sock = getSimulationSocket();
    if (sock) sock.resume();
    else await simResume();
  };

  const stop = async () => {
    setSimStatus('stopped');
    setStatus('STOPPED');
    const sock = getSimulationSocket();
    if (sock) sock.stop();
    else await simStop();
  };

  const restart = async () => {
    if (!trajectory) return;
    const sock = getSimulationSocket();
    if (sock) sock.stop();
    await new Promise((r) => setTimeout(r, 60));
    await play();
  };

  return (
    <div className="card">
      <div className="spread">
        <div className="btn-row">
          <button className="btn primary" onClick={play} disabled={!trajectory || simStatus === 'running'}>
            ▶ Play
          </button>
          <button className="btn" onClick={pause} disabled={simStatus !== 'running'}>
            ⏸ Pause
          </button>
          <button className="btn" onClick={resume} disabled={simStatus !== 'paused'}>
            ▶ Resume
          </button>
          <button className="btn danger" onClick={stop} disabled={simStatus !== 'running' && simStatus !== 'paused'}>
            ⏹ Stop
          </button>
          {withRestart && (
            <button className="btn" onClick={restart} disabled={!trajectory}>
              ↻ Restart
            </button>
          )}
        </div>
        <div className="mono" style={{ fontSize: 13 }}>
          Simulation Time:{' '}
          <span className="accent">{simTime.toFixed(2)}</span>
          <span className="muted"> / {duration.toFixed(2)} s</span>
        </div>
      </div>
      <div className="progress-track mt">
        <div className="progress-fill" style={{ width: `${Math.min(100, progress * 100)}%` }} />
      </div>
    </div>
  );
}
