import type { Vec3 } from '../types/robot';
import type { SimulationStatus } from '../types/trajectory';

export interface SimulationFrame {
  type: 'frame';
  status: string;
  time: number;
  duration: number;
  progress: number;
  q_rad: number[];
  q_deg: number[];
  position: Vec3;
}

export interface SimulationStatusMessage {
  type: 'status';
  simulation: SimulationStatus;
  q_deg?: number[];
}

type Message = SimulationFrame | SimulationStatusMessage | { type: 'pong' };

/**
 * WebSocket client for the live simulation stream.
 * Reconnects automatically and exposes a tiny command API.
 */
export class SimulationSocket {
  private ws: WebSocket | null = null;
  private closedByUser = false;
  private reconnectTimer: number | null = null;

  constructor(
    private onFrame: (frame: SimulationFrame) => void,
    private onStatus: (status: SimulationStatus) => void,
    private onConnectionChange: (connected: boolean) => void,
  ) {}

  connect(): void {
    if (this.ws && this.ws.readyState <= WebSocket.OPEN) return;
    this.closedByUser = false;
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const url = `${proto}://${window.location.host}/ws/simulation`;
    const ws = new WebSocket(url);
    this.ws = ws;

    ws.onopen = () => this.onConnectionChange(true);
    ws.onclose = () => {
      this.onConnectionChange(false);
      if (!this.closedByUser) {
        this.reconnectTimer = window.setTimeout(() => this.connect(), 1500);
      }
    };
    ws.onerror = () => ws.close();
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data as string) as Message;
        if (msg.type === 'frame') this.onFrame(msg);
        else if (msg.type === 'status') this.onStatus(msg.simulation);
      } catch {
        /* ignore malformed messages */
      }
    };
  }

  private send(payload: Record<string, unknown>): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload));
    }
  }

  start(trajectoryId?: string, speed = 1): void {
    this.send({ type: 'start', trajectory_id: trajectoryId ?? null, speed });
  }

  pause(): void {
    this.send({ type: 'pause' });
  }

  resume(): void {
    this.send({ type: 'resume' });
  }

  stop(): void {
    this.send({ type: 'stop' });
  }

  disconnect(): void {
    this.closedByUser = true;
    if (this.reconnectTimer !== null) window.clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }
}
