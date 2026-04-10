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
    } finally {
      setIsLoading(false);
    }
  }

  function handleComposerKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (!isLoading && draft.trim()) {
        void handleSubmit(event);
      }
    }
  }

  return (
    <main className="terminal-shell">
      <header className="terminal-header">
        <div>
          <p className="terminal-kicker">repo analyser</p>
          <h1>Agent Console</h1>
        </div>
      </header>

      <section className="chat-log" role="log" aria-live="polite">
        {deferredMessages.map((message) => (
          <MessageRow key={message.id} message={message} />
        ))}

        {isLoading ? (
          <article className="message-row assistant">
            <div className="message-head">
              <AgentBadge trace={[]} loading />
            </div>
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
          onKeyDown={handleComposerKeyDown}
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

function MessageRow({ message }) {
  return (
    <article className={`message-row ${message.role}`}>
      <div className="message-head">
        {message.role === "assistant" ? (
          <AgentBadge trace={message.trace ?? []} />
        ) : (
          <div className="user-badge">
            <span className="user-avatar">01</span>
            <span className="message-role">you</span>
          </div>
        )}
      </div>
      <pre className="message-content">{message.content}</pre>
    </article>
  );
}

function AgentBadge({ trace, loading = false }) {
  const hasTrace = trace.length > 0;

  return (
    <div className="agent-badge" tabIndex={0}>
      <span className="agent-avatar" aria-hidden="true">
        [bot]
      </span>
      <span className="message-role">agent</span>

      {loading ? <span className="agent-meta">working</span> : null}

      {hasTrace ? (
        <div className="trace-popover" role="note">
          <p className="trace-heading">reasoning summary</p>
          {trace.map((entry, index) => (
            <div className="trace-line" key={entry.id ?? `${entry.tool}-${index}`}>
              <p className="trace-line-title">
                {index + 1}. {entry.tool} <span>{entry.kind === "thought" ? "reasoning" : "tool"}</span>
              </p>
              <p className="trace-line-copy">{entry.label}</p>
              {entry.output ? <pre>{formatTraceOutput(entry.output)}</pre> : null}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function formatTraceOutput(output) {
  const trimmed = output.trim();
  if (!trimmed) {
    return "";
  }
  if (trimmed.length <= 280) {
    return trimmed;
  }
  return `${trimmed.slice(0, 280)}...`;
}

export default App;
