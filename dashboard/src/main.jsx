import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./styles.css";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error("Dashboard render error", error, info);
  }

  render() {
    if (this.state.error) {
      return React.createElement(
        "main",
        { className: "app-shell centered error-screen" },
        React.createElement(
          "div",
          null,
          React.createElement("h1", null, "Dashboard render error"),
          React.createElement("p", null, this.state.error.message)
        )
      );
    }

    return this.props.children;
  }
}

createRoot(document.getElementById("root")).render(
  React.createElement(
    React.StrictMode,
    null,
    React.createElement(
      ErrorBoundary,
      null,
      React.createElement(App)
    )
  )
);
