import { Link } from 'react-router-dom';

import ParameterCard from '../../components/ParameterCard/ParameterCard';
import RobotViewer from '../../components/RobotViewer/RobotViewer';
import { useRobotStore } from '../../store/robotStore';
import './Overview.css';

export default function Overview() {
  const info = useRobotStore((s) => s.info);
  const specs = info?.official_specs;

  return (
    <div className="page overview">
      <div className="overview-hero">
        <div>
          <h1 className="overview-title">
            APE 6-DOF INDUSTRIAL ROBOT
            <br />
            SIMULATION PLATFORM
          </h1>
          <p className="overview-lead">
            An interactive, computation-backed simulation of the{' '}
            <strong>{specs?.model ?? 'APE SV2-6045'}</strong> vertical articulated
            robot. All kinematics, workspace, trajectory and dynamics results are
            computed by the Python robotics engine — nothing is animated without
            real mathematics behind it.
          </p>
          <div className="btn-row mt">
            <Link to="/dashboard" className="btn primary">
              Start Simulation →
            </Link>
            <Link to="/documentation" className="btn ghost">
              Read the Documentation
            </Link>
          </div>
        </div>
        <div className="overview-viewer">
          <RobotViewer height={330} />
        </div>
      </div>

      <div className="grid cols-4 mt">
        <ParameterCard value={specs?.dof ?? 6} label="Degrees of Freedom" />
        <ParameterCard value={specs?.payload_rated_kg ?? 1} unit="kg" label="Rated Payload" />
        <ParameterCard value={Math.round((specs?.max_radius_m ?? 0.454) * 1000)} unit="mm" label="Max. Radius" />
        <ParameterCard value={`±${specs?.repeatability_mm ?? 0.02}`} unit="mm" label="Repeatability" />
      </div>

      <div className="grid cols-2 mt">
        <div className="card">
          <div className="card-title">About the Robot</div>
          <ul className="overview-list">
            <li>
              The {specs?.model ?? 'SV2-6045'} is a {specs?.dof ?? 6}-axis vertical
              articulated industrial robot by {specs?.manufacturer ?? 'APE Technology'}.
            </li>
            <li>
              It is used here as the reference model for a university Robotics
              project: DH modelling, forward/inverse kinematics, workspace,
              trajectory planning and dynamics.
            </li>
            <li>
              Official specifications (payload, reach, joint ranges, repeatability)
              are taken from the APE product data. Kinematic (DH) and dynamic
              parameters are <em>educational estimates</em>, since APE does not
              publish them — this is labeled everywhere in the app.
            </li>
            <li>
              All results depend on the parameters loaded in the system and can be
              inspected on the <Link to="/dh">DH Model</Link> page.
            </li>
          </ul>
        </div>
        <div className="card">
          <div className="card-title">About the Project</div>
          <p className="overview-text">
            This project implements a complete simulation pipeline for a 6-DOF
            industrial robot using Python and a modern web-based interface. The
            system includes DH modeling, forward kinematics, inverse kinematics,
            workspace analysis, trajectory planning, joint motion analysis,
            dynamics, torque calculation, and interactive 3D visualization.
          </p>
          <p className="overview-text muted">
            Python (FastAPI · NumPy · SciPy · Robotics Toolbox · SpatialMath)
            performs every computation. React + Three.js render the results and
            stream the live simulation over WebSocket.
          </p>
          <div className="note mt">
            Parameter source: kinematics — {info?.kinematic_parameter_source ?? 'Educational / Assumed'} ·
            dynamics — {info?.dynamic_parameter_source ?? 'Educational / Assumed'}
          </div>
        </div>
      </div>

      <div className="grid cols-3 mt">
        <ParameterCard value="12" label="Interactive Pages" accent={false} />
        <ParameterCard value={specs?.body_weight_kg ?? 23} unit="kg" label="Body Weight" accent={false} />
        <ParameterCard value={specs?.joint_speeds_deg_s?.[5] ?? 600} unit="°/s" label="Max Joint Speed (J6)" accent={false} />
      </div>
    </div>
  );
}
