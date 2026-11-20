declare module 'plotly.js-dist-min' {
  export interface PlotlyTrace {
    x: ArrayLike<number>;
    y: ArrayLike<number>;
    name?: string;
    mode?: string;
    type?: string;
    line?: { color?: string; width?: number };
  }

  export interface PlotlyLayout {
    template?: string;
    paper_bgcolor?: string;
    plot_bgcolor?: string;
    font?: { color?: string; family?: string; size?: number };
    margin?: { l?: number; r?: number; t?: number; b?: number };
    xaxis?: { title?: { text?: string }; gridcolor?: string; zerolinecolor?: string };
    yaxis?: { title?: { text?: string }; gridcolor?: string; zerolinecolor?: string };
    legend?: { orientation?: string; bgcolor?: string; font?: { size?: number } };
    showlegend?: boolean;
    height?: number;
  }

  const Plotly: {
    newPlot: (
      el: HTMLElement,
      data: PlotlyTrace[],
      layout?: PlotlyLayout,
      config?: Record<string, unknown>,
    ) => Promise<unknown>;
    react: (
      el: HTMLElement,
      data: PlotlyTrace[],
      layout?: PlotlyLayout,
      config?: Record<string, unknown>,
    ) => Promise<unknown>;
    purge: (el: HTMLElement) => void;
  };

  export default Plotly;
}
