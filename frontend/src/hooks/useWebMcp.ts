import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";

export function useWebMcp() {
  const navigate = useNavigate();
  useEffect(() => {
    const context = document.modelContext;
    if (!context?.registerTool) return;
    const lifecycle = new AbortController();
    const register = async () => {
      await Promise.resolve(
        context.registerTool(
          {
            name: "start_voice_risk_demo",
            title: "Start voice-risk demo",
            description: "Start one named Phantom Vox judge scenario and return its stored session state.",
            inputSchema: {
              type: "object",
              properties: {
                scenario: {
                  type: "string",
                  enum: ["genuine", "mid_call_clone", "poor_quality", "high_context_uncertain"],
                },
              },
              required: ["scenario"],
              additionalProperties: false,
            },
            annotations: { readOnlyHint: false, untrustedContentHint: false },
            execute: async (input) => {
              const scenario = (input as { scenario?: string }).scenario;
              if (!scenario) throw new Error("scenario is required");
              const result = await api.startDemo(scenario, true);
              navigate(`/live-guard?session=${result.session.id}`);
              return { session_id: result.session.id, state: result.session.state, risk_index: result.session.risk_index };
            },
          },
          { signal: lifecycle.signal },
        ),
      );
      await Promise.resolve(
        context.registerTool(
          {
            name: "navigate_phantom_vox",
            title: "Open Phantom Vox workspace",
            description: "Navigate to one of the visible Phantom Vox product workspaces.",
            inputSchema: {
              type: "object",
              properties: {
                workspace: {
                  type: "string",
                  enum: ["overview", "live-guard", "investigations", "trusted-voices", "policies", "integrations", "model-trust", "privacy-audit"],
                },
              },
              required: ["workspace"],
              additionalProperties: false,
            },
            annotations: { readOnlyHint: true, untrustedContentHint: false },
            execute: (input) => {
              const workspace = (input as { workspace?: string }).workspace;
              if (!workspace) throw new Error("workspace is required");
              navigate(`/${workspace}`);
              return { navigated_to: workspace };
            },
          },
          { signal: lifecycle.signal },
        ),
      );
    };
    void register().catch(() => undefined);
    return () => lifecycle.abort();
  }, [navigate]);
}
