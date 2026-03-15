"use client";

import React from "react";

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            position: "fixed",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            background: "#09090b",
            color: "#fafafa",
            fontFamily: "Inter, system-ui, sans-serif",
            gap: "1rem",
          }}
        >
          <h2 style={{ margin: 0 }}>Something went wrong</h2>
          <p style={{ color: "#a1a1aa", maxWidth: 400, textAlign: "center" }}>
            {this.state.error?.message ?? "An unexpected error occurred."}
          </p>
          <button
            type="button"
            className="btn btn-primary"
            onClick={this.handleRetry}
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
