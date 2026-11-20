import { useRobotStore } from '../../store/robotStore';
import './JointControls.css';

interface Props {
  disabled?: boolean;
}

/** Six joint sliders + numeric inputs, always within published limits. */
export default function JointControls({ disabled = false }: Props) {
  const qDeg = useRobotStore((s) => s.qDeg);
  const info = useRobotStore((s) => s.info);
  const setJoints = useRobotStore((s) => s.setJoints);

  const limits = info?.joint_limits_deg ?? Array.from({ length: 6 }, () => [-180, 180] as [number, number]);

  const update = (index: number, value: number) => {
    if (!Number.isFinite(value)) return;
    const next = [...qDeg];
    next[index] = Math.min(Math.max(value, limits[index][0]), limits[index][1]);
    void setJoints(next);
  };

  return (
    <div className="joint-controls">
      {qDeg.map((value, i) => (
        <div className="joint-row" key={i}>
          <div className="joint-name">J{i + 1}</div>
          <div className="joint-slider">
            <input
              type="range"
              min={limits[i][0]}
              max={limits[i][1]}
              step={0.1}
              value={value}
              disabled={disabled}
              onChange={(e) => update(i, Number(e.target.value))}
            />
            <div className="joint-range mono">
              {limits[i][0]}° <span /> +{limits[i][1]}°
            </div>
          </div>
          <input
            className="input joint-input"
            type="number"
            min={limits[i][0]}
            max={limits[i][1]}
            step={0.1}
            value={Number(value.toFixed(2))}
            disabled={disabled}
            onChange={(e) => update(i, Number(e.target.value))}
          />
          <span className="joint-unit">°</span>
        </div>
      ))}
    </div>
  );
}
