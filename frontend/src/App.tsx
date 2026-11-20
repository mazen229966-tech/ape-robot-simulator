import { useEffect } from 'react';
import { Route, Routes } from 'react-router-dom';

import Header from './components/Header/Header';
import Sidebar from './components/Sidebar/Sidebar';
import { useSimulationSocket } from './hooks/useSimulationSocket';
import Dashboard from './pages/Dashboard/Dashboard';
import DHModel from './pages/DHModel/DHModel';
import Documentation from './pages/Documentation/Documentation';
import DrawH from './pages/DrawH/DrawH';
import Dynamics from './pages/Dynamics/Dynamics';
import ForwardKinematics from './pages/ForwardKinematics/ForwardKinematics';
import InverseKinematics from './pages/InverseKinematics/InverseKinematics';
import MotionAnalysis from './pages/MotionAnalysis/MotionAnalysis';
import Overview from './pages/Overview/Overview';
import RobotControl from './pages/RobotControl/RobotControl';
import Settings from './pages/Settings/Settings';
import Trajectory from './pages/Trajectory/Trajectory';
import Workspace from './pages/Workspace/Workspace';
import { useRobotStore } from './store/robotStore';

export default function App() {
  const fetchRobot = useRobotStore((s) => s.fetchRobot);
  const fetchDH = useRobotStore((s) => s.fetchDH);
  const loaded = useRobotStore((s) => s.loaded);
  const errorMsg = useRobotStore((s) => s.errorMsg);

  // single WebSocket for the whole app + initial robot data load
  useSimulationSocket();

  useEffect(() => {
    void fetchRobot();
    void fetchDH().catch(() => undefined);
  }, [fetchRobot, fetchDH]);

  return (
    <div>
      <Sidebar />
      <Header />
      <main style={{ marginLeft: 'var(--sidebar-w)', paddingTop: 'var(--header-h)' }}>
        {!loaded && <div className="page muted">Connecting to the robotics engine…</div>}
        {loaded && errorMsg && (
          <div className="page">
            <div className="msg error">⚠ {errorMsg} — is the backend running on port 8000?</div>
          </div>
        )}
        {loaded && !errorMsg && (
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/dh" element={<DHModel />} />
            <Route path="/control" element={<RobotControl />} />
            <Route path="/forward-kinematics" element={<ForwardKinematics />} />
            <Route path="/inverse-kinematics" element={<InverseKinematics />} />
            <Route path="/workspace" element={<Workspace />} />
            <Route path="/trajectory" element={<Trajectory />} />
            <Route path="/motion-analysis" element={<MotionAnalysis />} />
            <Route path="/dynamics" element={<Dynamics />} />
            <Route path="/draw-h" element={<DrawH />} />
            <Route path="/documentation" element={<Documentation />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        )}
      </main>
    </div>
  );
}
