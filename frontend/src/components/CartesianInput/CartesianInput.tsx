export interface CartesianValue {
  x: number;
  y: number;
  z: number;
}

interface Props {
  value: CartesianValue;
  onChange: (v: CartesianValue) => void;
  unit?: string;
  labels?: [string, string, string];
}

/** Compact X/Y/Z numeric input group. */
export default function CartesianInput({
  value,
  onChange,
  unit = 'mm',
  labels = ['X', 'Y', 'Z'],
}: Props) {
  const keys: (keyof CartesianValue)[] = ['x', 'y', 'z'];
  return (
    <div className="grid cols-3">
      {keys.map((k, i) => (
        <div key={k}>
          <label className="field-label">
            {labels[i]} ({unit})
          </label>
          <input
            className="input"
            type="number"
            step={1}
            value={value[k]}
            onChange={(e) => onChange({ ...value, [k]: Number(e.target.value) })}
          />
        </div>
      ))}
    </div>
  );
}
