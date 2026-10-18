import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { ErrorBoundary } from "./components/ErrorBoundary";
import "./styles.css";
// Adapt dialogs and navigation to the visible Android viewport while an input
// opens the keyboard. Browser zoom and physical keyboards remain usable.
const adaptViewport=()=>{
  const viewport=window.visualViewport;
  if(!viewport)return;
  document.documentElement.style.setProperty('--visual-height',`${viewport.height}px`);
  const editing=document.activeElement?.matches('input,textarea,[contenteditable="true"]');
  document.documentElement.classList.toggle('keyboard-open',!!editing&&viewport.height<window.innerHeight*.75);
};
window.visualViewport?.addEventListener('resize',adaptViewport);
document.addEventListener('focusin',adaptViewport);
document.addEventListener('focusout',()=>requestAnimationFrame(adaptViewport));
adaptViewport();
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);
if ("serviceWorker" in navigator && import.meta.env.PROD) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register(`${import.meta.env.BASE_URL}sw.js`, {
        scope: import.meta.env.BASE_URL,
      })
      .catch(() => {
        console.warn("PULSE offline installation unavailable");
      });
  });
}
