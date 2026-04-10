import { startTransition, useDeferredValue, useState } from "react";

const API_URL = "/api/chat";

const INITIAL_MESSAGES = [
  {
    id: "welcome",
    role: "assistant",
    content: "Repo analyser ready. Ask a question about a repository.",
    toolsUsed: [],
    trace: [],
  },
];

function App() {
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [draft, setDraft] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [traceVisible, setTraceVisible] = useState(false);
  const [status, setStatus] = useState("idle");
  const deferredMessages = useDeferredValue(messages);

  async function handleSubmit(event) {
    event.preventDefault();
    const prompt = draft.trim();
    if (!prompt || isLoading) {
      return;
    }

    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: prompt,
    };

    setDraft("");
    setIsLoading(true);
    setStatus("thinking");
    startTransition(() => {
      setMessages((current) => [...current, userMessage]);
    });

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: prompt }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data = await response.json();
      const assistantMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.answer ?? "No answer returned.",
        toolsUsed: Array.isArray(data.toolsUsed) ? data.toolsUsed : [],
        trace: Array.isArray(data.trace) ? data.trace : [],
      };

      startTransition(() => {
        setMessages((current) => [...current, assistantMessage]);
      });
      setStatus("ready");
    } catch (error) {
      startTransition(() => {
        setMessages((current) => [
          ...current,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content:
              error instanceof Error
                ? `Connection problem: ${error.message}`
                : "Connection problem.",
            toolsUsed: [],
            trace: [],
          },
        ]);
      });
      setStatus("error");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="terminal-shell">
      <header className="terminal-header">
        <div>
          <p className="terminal-kicker">repo analyser</p>
          <h1>Agent Console</h1>
        </div>
        <div className="terminal-controls">
          <span className="status-pill">status: {status}</span>
          <button
            className="toggle-button"
            type="button"
            onClick={() => setTraceVisible((current) => !current)}
            aria-pressed={traceVisible}
          >
            {traceVisible ? "hide trace" : "show trace"}
          </button>
        </div>
      </header>

      <section className="chat-log" role="log" aria-live="polite">
        {deferredMessages.map((message) => (
          <MessageRow key={message.id} message={message} traceVisible={traceVisible} />
        ))}

        {isLoading ? (
          <article className="message-row assistant">
            <p className="message-role">agent</p>
            <pre className="message-content">thinking...</pre>
          </article>
        ) : null}
      </section>

      <form className="composer" onSubmit={handleSubmit}>
        <label className="sr-only" htmlFor="prompt">
          Prompt
        </label>
        <textarea
          id="prompt"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Ask about a repository..."
          rows={5}
        />
        <div className="composer-footer">
          <span className="composer-hint">Enter to send. Shift+Enter for a new line.</span>
          <button className="send-button" type="submit" disabled={isLoading || !draft.trim()}>
            send
          </button>
        </div>
      </form>
    </main>
  );
}

function MessageRow({ message, traceVisible }) {
  const hasTrace = message.role === "assistant" && message.trace?.length;

  return (
    <article className={`message-row ${message.role}`}>
      <p className="message-role">{message.role === "assistant" ? "agent" : "you"}</p>
      <pre className="message-content">{message.content}</pre>

      {traceVisible && hasTrace ? (
        <div className="trace-block">
          <p className="trace-heading">trace</p>
          {message.trace.map((entry, index) => (
            <details className="trace-entry" key={entry.id ?? `${entry.tool}-${index}`}>
              <summary>
                <span>{index + 1}. {entry.tool}</span>
                <span>{entry.kind === "thought" ? "reasoning" : "tool"}</span>
              </summary>
              <div className="trace-detail">
                <p>{entry.label}</p>
                <pre>{formatTraceDetail(entry)}</pre>
              </div>
            </details>
          ))}
        </div>
      ) : null}
    </article>
  );
}

function formatTraceDetail(entry) {
  const input = entry.input ? JSON.stringify(entry.input, null, 2) : "{}";
  const output = entry.output || "No output";
  return `input\n${input}\n\noutput\n${output}`;
}

export default App;
