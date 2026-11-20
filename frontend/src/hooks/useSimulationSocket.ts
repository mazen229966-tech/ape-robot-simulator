import { useEffect, useRef } from 'react';

import { SimulationSocket } from '../services/websocket';
import { useSimulationStore } from '../store/simulationStore';

let socket: SimulationSocket | null = null;

export function getSimulationSocket(): SimulationSocket | null {
  return socket;
}

/**
 * Opens the simulation WebSocket once for the whole app and routes
 * incoming frames/status messages into the simulation store.
 */
export function useSimulationSocket(): void {
  const applyFrame = useSimulationStore((s) => s.applyFrame);
  const setSimStatus = useSimulationStore((s) => s.setSimStatus);
  const setConnected = useSimulationStore((s) => s.setConnected);
  const refs = useRef({ applyFrame, setSimStatus, setConnected });
  refs.current = { applyFrame, setSimStatus, setConnected };

  useEffect(() => {
    socket = new SimulationSocket(
      (frame) => refs.current.applyFrame(frame),
      (status) => refs.current.setSimStatus(status.status),
      (connected) => refs.current.setConnected(connected),
    );
    socket.connect();
    return () => {
      socket?.disconnect();
      socket = null;
    };
  }, []);
}
