/**
 * The workshop modules shown in "Hands-on labs" and in llms.txt.
 * Source: the lab guides in next-gen-governance (services/ui_frontend/src/lib/labs/content/labs/*.mdx),
 * grouped by hand into modules. Update here when a lab is added or renamed there.
 */
export interface Module { title: string; topics: string[]; labs: string[] }

export const modules: Module[] = [
  { title: 'Context Engineering for Coding Agents', topics: ['Context files', 'Prompting', 'Spec-driven development', 'Skills', 'DSPy', 'GEPA'],
    labs: ['Foundations & Context Engineering, Part 1', 'Foundations & Context Engineering, Part 2', 'Skills, MCP & Spec-Driven Development', 'Compiling prompts with DSPy', 'Evolving text with GEPA'] },
  { title: 'Hooks, Guardrails & Policy as Code', topics: ['Hooks', 'Self-validating loops', 'Requirements', 'Output validation', 'Zenable'],
    labs: ['Hooks, Guardrails & Policy Enforcement', 'Enforcing requirements on LLMs', 'Validating AI outputs', 'What Zenable Does'] },
  { title: 'MCP, Agent Protocols & Identity', topics: ['MCP', 'OAuth 2.1', 'agentgateway', 'A2A', 'ACP', 'DPoP', 'AAuth'],
    labs: ['Getting Started with MCP', 'MCP Enterprise Authorization', 'Governing MCP traffic with agentgateway', 'Hands-on with A2A', 'Agent Client Protocol', 'DPoP token binding and SD-JWT', 'Hands-on with Agent Auth (AAuth)'] },
  { title: 'Runtime Observability & Sandboxing', topics: ['Telemetry', 'seccomp', 'eBPF', 'Tetragon', 'Landlock'],
    labs: ['Observability & Measurement', 'Syscalls and seccomp', 'eBPF from scratch: watch an agent, then stop it', 'Runtime enforcement with Tetragon, OpenTelemetry, and nono'] },
  { title: 'Formal Verification & Typed Evals', topics: ['Lean', 'Typed questions', 'Model routing', 'Refactoring'],
    labs: ['Formally verifying software with Lean', 'Typed questions for code (Jev)', 'Routing model traffic with Jev and agentgateway', 'Refactoring for the next change'] },
  { title: 'Agent Teams & Orchestration', topics: ['Agent teams', 'Improvement flywheel', 'Orchestrators', 'Gastown', 'LSP'],
    labs: ['Agents, Teams & Continuous Improvement', 'Orchestrators & Gastown', 'Code intelligence for Claude Code with LSP'] },
  { title: 'Inside the Model', topics: ['Refusal', 'Embeddings', 'LoRA', 'An LLM from scratch'],
    labs: ['AI Refusal: find it, cancel it, build it', 'Vectors and embeddings', 'LoRA and fine-tuning', 'An LLM from scratch'] },
];
