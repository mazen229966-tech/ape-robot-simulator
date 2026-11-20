import { NavLink } from 'react-router-dom';
import './Sidebar.css';

interface NavItem {
  to: string;
  label: string;
  icon: string;
}

interface NavSection {
  title?: string;
  items: NavItem[];
}

const SECTIONS: NavSection[] = [
  {
    items: [
      { to: '/', label: 'Overview', icon: '🤖' },
      { to: '/dashboard', label: 'Dashboard', icon: '📊' },
    ],
  },
  {
    title: 'Robot Model',
    items: [
      { to: '/dh', label: 'DH Model', icon: '📐' },
      { to: '/control', label: 'Robot Control', icon: '🎮' },
    ],
  },
  {
    title: 'Kinematics',
    items: [
      { to: '/forward-kinematics', label: 'Forward', icon: '➡' },
      { to: '/inverse-kinematics', label: 'Inverse', icon: '⬅' },
    ],
  },
  {
    title: 'Motion',
    items: [
      { to: '/workspace', label: 'Workspace', icon: '🌐' },
      { to: '/trajectory', label: 'Trajectory', icon: '🛣' },
      { to: '/motion-analysis', label: 'Motion Analysis', icon: '📈' },
    ],
  },
  {
    title: 'Dynamics',
    items: [{ to: '/dynamics', label: 'Dynamics', icon: '⚙' }],
  },
  {
    title: 'Demo',
    items: [{ to: '/draw-h', label: 'Draw H', icon: '✏' }],
  },
  {
    items: [
      { to: '/documentation', label: 'Documentation', icon: '📖' },
      { to: '/settings', label: 'Settings', icon: '⚙' },
    ],
  },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-mark">APE</div>
        <div>
          <div className="brand-title">6-DOF ROBOT</div>
          <div className="brand-sub">SIMULATION PLATFORM</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {SECTIONS.map((section, si) => (
          <div key={si}>
            {section.title && (
              <div className="nav-section-title">{section.title}</div>
            )}
            {section.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `nav-item${isActive ? ' active' : ''}`
                }
                title={item.label}
              >
                <span className="nav-icon">{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        Simulation only — no hardware control
      </div>
    </aside>
  );
}
