interface Props {
  selection: number | 'all';
  onChange: (s: number | 'all') => void;
}

const COLORS = ['#38bdf8', '#34d399', '#fbbf24', '#f87171', '#a78bfa', '#f472b6'];

export const JOINT_COLORS = COLORS;

/** J1..J6 / ALL toggle group for joint-based charts. */
export default function JointSeriesSelector({ selection, onChange }: Props) {
  return (
    <div className="btn-row">
      {[0, 1, 2, 3, 4, 5].map((j) => (
        <button
          key={j}
          className={`btn sm${selection === j ? ' primary' : ''}`}
          style={selection === j ? { borderColor: COLORS[j], color: COLORS[j] } : undefined}
          onClick={() => onChange(j)}
        >
          J{j + 1}
        </button>
      ))}
      <button
        className={`btn sm${selection === 'all' ? ' primary' : ''}`}
        onClick={() => onChange('all')}
      >
        ALL
      </button>
    </div>
  );
}
