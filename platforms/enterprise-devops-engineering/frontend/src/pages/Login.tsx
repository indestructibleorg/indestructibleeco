import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";

const API_BASE = "";

export default function Login() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const endpoint = mode === "login" ? "/auth/login" : "/auth/signup";
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.message || data.error || "Authentication failed");
        return;
      }

      if (data.session?.access_token) {
        localStorage.setItem("eco_token", data.session.access_token);
        localStorage.setItem("eco_refresh_token", data.session.refresh_token || "");
        localStorage.setItem("eco_user", JSON.stringify(data.user));
        navigate("/");
      } else if (mode === "signup") {
        setError("Account created. Check your email to confirm, then log in.");
        setMode("login");
      }
    } catch (err) {
      setError("Network error. Is the API server running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--color-bg, #06060F)",
        fontFamily: "monospace",
      }}
    >
      <div
        style={{
          width: 400,
          padding: 32,
          borderRadius: 12,
          background: "var(--color-surface, #0D0D1A)",
          border: "1px solid #1a1a2e",
        }}
      >
        <h1
          style={{
            color: "var(--color-primary, #00F5D4)",
            fontSize: 24,
            marginBottom: 4,
          }}
        >
          indestructibleeco
        </h1>
        <p style={{ color: "var(--color-muted, #6B7A99)", marginBottom: 24, fontSize: 14 }}>
          {mode === "login" ? "Sign in to your account" : "Create a new account"}
        </p>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div>
            <label
              htmlFor="email"
              style={{ display: "block", color: "#9CA3AF", fontSize: 12, marginBottom: 4 }}
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: 6,
                border: "1px solid #2a2a3e",
                background: "#0a0a14",
                color: "#E0E0E0",
                fontSize: 14,
                outline: "none",
              }}
            />
          </div>

          <div>
            <label
              htmlFor="password"
              style={{ display: "block", color: "#9CA3AF", fontSize: 12, marginBottom: 4 }}
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: 6,
                border: "1px solid #2a2a3e",
                background: "#0a0a14",
                color: "#E0E0E0",
                fontSize: 14,
                outline: "none",
              }}
            />
          </div>

          {error && (
            <p style={{ color: "var(--color-danger, #F72585)", fontSize: 13 }}>{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              padding: "10px 0",
              borderRadius: 6,
              border: "none",
              background: loading ? "#2a2a3e" : "var(--color-accent, #4361EE)",
              color: "#fff",
              fontSize: 14,
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "..." : mode === "login" ? "Sign In" : "Create Account"}
          </button>
        </form>

        <p style={{ color: "#6B7A99", fontSize: 12, marginTop: 16, textAlign: "center" }}>
          {mode === "login" ? (
            <>
              No account?{" "}
              <button
                onClick={() => { setMode("signup"); setError(""); }}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--color-primary, #00F5D4)",
                  cursor: "pointer",
                  fontSize: 12,
                }}
              >
                Sign up
              </button>
            </>
          ) : (
            <>
              Have an account?{" "}
              <button
                onClick={() => { setMode("login"); setError(""); }}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--color-primary, #00F5D4)",
                  cursor: "pointer",
                  fontSize: 12,
                }}
              >
                Sign in
              </button>
            </>
          )}
        </p>
      </div>
    </main>
  );
}
