import { Component, type ErrorInfo, type ReactNode } from "react";
export class ErrorBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch(_error: Error, _info: ErrorInfo) {
    console.error("PULSE screen could not render");
  }
  render() {
    return this.state.failed ? (
      <main>
        <h1>לא ניתן להציג את המסך</h1>
        <p>טענו מחדש את האפליקציה כדי לנסות שוב. המידע השמור במכשיר לא נמחק.</p>
        <button className="primary" onClick={() => location.reload()}>
          טעינה מחדש
        </button>
      </main>
    ) : (
      this.props.children
    );
  }
}
