"use client";

import { useEffect } from "react";

/**
 * Last-resort boundary for errors in the root layout itself. It replaces
 * the root layout entirely, so it must render its own <html> and <body>,
 * and it cannot rely on the app's fonts, theme variables or components.
 * Styles are inline and the colours are copied from globals.css.
 */
export default function GlobalError({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          minHeight: "100dvh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "48px 16px",
          background: "#f6f8f6",
          color: "#12211c",
          fontFamily: "ui-sans-serif, system-ui, sans-serif",
          fontSize: 14,
          lineHeight: 1.5,
        }}
      >
        <title>Something went wrong · ClinicFlow</title>
        <main style={{ width: "100%", maxWidth: 384 }}>
          <p style={{ margin: 0, fontWeight: 600, color: "#0f5c4c" }}>
            ClinicFlow
          </p>
          <h1 style={{ margin: "32px 0 0", fontSize: 22, fontWeight: 600 }}>
            Something went wrong
          </h1>
          <p style={{ margin: "8px 0 0", color: "#5a6b64" }}>
            ClinicFlow couldn&apos;t load. Please try again in a moment.
          </p>
          {error.digest && (
            <p style={{ margin: "12px 0 0", fontSize: 13, color: "#8a9993" }}>
              Reference: {error.digest}
            </p>
          )}
          <button
            type="button"
            onClick={() => retry()}
            style={{
              marginTop: 24,
              height: 36,
              padding: "0 16px",
              border: 0,
              borderRadius: 6,
              background: "#0f5c4c",
              color: "#fff",
              font: "inherit",
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            Try again
          </button>
        </main>
      </body>
    </html>
  );
}
