import React from "react";
import ReactDOM from "react-dom/client";
import App       from "./App.jsx";
import LoginGate from "./components/LoginGate.jsx";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <LoginGate>
      <App />
    </LoginGate>
  </React.StrictMode>
);
