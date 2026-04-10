import { startTransition, useDeferredValue, useEffect, useRef, useState } from "react";

const API_URL = "/api/chat";

const INITIAL_MESSAGES = [
  {
    id: "welcome",
    role: "assistant",
    content:
      "I’m ready to help you work through repositories. Ask a question, speak a prompt, or inspect the agent trace for tools and reasoning summaries.",
    toolsUsed: [],
    trace: [],
  },
];

function App() {
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [draft, setDraft] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [traceVisible, setTraceVisible] = useState(true);
  const [isListening, setIsListening] = useState(false);
  const [status, setStatus] = useState("Idle");
  const recognitionRef = useRef(null);
  const transcriptRef = useRef("");
  const deferredMessages = useDeferredValue(messages);

  const latestAssistant =
    [...deferredMessages].reverse().find((message) => message.role === "assistant") ?? null;

  useEffect(() => {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      return undefined;
    }

    const recognition = new Recognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onstart = () => {
      setIsListening(true);
      setStatus("Listening");
    };

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0]?.transcript ?? "")
        .join(" ")
        .trim();

      transcriptRef.current = transcript;
      startTransition(() => {
        setDraft(transcript);
      });
    };

    recognition.onend = () => {
      setIsListening(false);
      setStatus("Voice captured");
    };

    recognition.onerror = () => {
      setIsListening(false);
      setStatus("Voice unavailable");
    };

    recognitionRef.current = recognition;
    return () => {
      recognition.stop();
    };
  }, []);

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
    setStatus("Thinking");
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
      setStatus("Ready");
    } catch (error) {
      startTransition(() => {
        setMessages((current) => [
          ...current,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content:
              error instanceof Error
                ? `I hit a connection problem: ${error.message}`
                : "I hit a connection problem.",
            toolsUsed: [],
            trace: [],
          },
        ]);
      });
      setStatus("Connection issue");
    } finally {
      setIsLoading(false);
    }
  }

  function toggleListening() {
    const recognition = recognitionRef.current;
    if (!recognition) {
      setStatus("Speech recognition is not supported in this browser");
      return;
    }

    if (isListening) {
      recognition.stop();
      return;
    }

    transcriptRef.current = "";
    recognition.start();
  }

  function speakAnswer(text) {
    if (!("speechSynthesis" in window)) {
      setStatus("Speech playback is not supported in this browser");
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
    setStatus("Speaking");
  }

  return (
    <div className="app-shell">
      <div className="ambient ambient-left" />
      <div className="ambient ambient-right" />
      <header className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Voice-first repository workspace</p>
          <h1>Speak with your agent. Review its answer. Inspect its work.</h1>
          <p className="hero-text">
            The workspace keeps the chat readable, surfaces tools and findings, and lets you hide the reasoning layer whenever you just want the highlights.
          </p>
        </div>
        <div className="hero-panel" aria-label="Agent status">
          <div className="panel-orb" />
          <p className="panel-label">Live status</p>
          <p className="panel-value">{status}</p>
          <button
            className="panel-toggle"
            type="button"
            onClick={() => setTraceVisible((current) => !current)}
            aria-pressed={traceVisible}
          >
            {traceVisible ? "Hide trace layer" : "Show trace layer"}
          </button>
        </div>
      </header>

      <main className="workspace">
        <section className="chat-stage" aria-label="Conversation">
          <div className="chat-header">
            <div>
              <p className="section-label">Conversation</p>
              <h2>Readable answers, not a wall of text</h2>
            </div>
            <div className="chat-actions">
              <button
                className={`voice-button ${isListening ? "active" : ""}`}
                type="button"
                onClick={toggleListening}
              >
                {isListening ? "Stop listening" : "Speak to agent"}
              </button>
            </div>
          </div>

          <div className="messages" role="log" aria-live="polite">
            {deferredMessages.map((message) => (
              <MessageCard
                key={message.id}
                message={message}
                traceVisible={traceVisible}
                onSpeak={speakAnswer}
              />
            ))}
            {isLoading ? (
              <div className="message assistant pending">
                <div className="message-meta">Agent</div>
                <div className="message-body">Working through the request…</div>
              </div>
            ) : null}
          </div>

          <form className="composer" onSubmit={handleSubmit}>
            <label className="sr-only" htmlFor="prompt">
              Message the agent
            </label>
            <textarea
              id="prompt"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ask about a repository, request a download, or search the web…"
              rows={4}
            />
            <div className="composer-actions">
              <p className="composer-hint">
                {recognitionRef.current
                  ? "Voice input is available in this browser."
                  : "Voice input depends on browser speech recognition support."}
              </p>
              <button className="submit-button" type="submit" disabled={isLoading || !draft.trim()}>
                Send prompt
              </button>
            </div>
          </form>
        </section>

        <aside className="inspector" aria-label="Agent details">
          <div className="inspector-block">
            <p className="section-label">Hot topics</p>
            <h3>Most recent tool activity</h3>
            <div className="chip-row">
              {latestAssistant?.toolsUsed?.length ? (
                latestAssistant.toolsUsed.map((toolName) => (
                  <span className="chip" key={toolName}>
                    {toolName}
                  </span>
                ))
              ) : (
                <span className="muted">No tools used in the latest answer yet.</span>
              )}
            </div>
          </div>

          <div className="inspector-block">
            <p className="section-label">Reasoning layer</p>
            <h3>{traceVisible ? "Visible" : "Hidden"}</h3>
            <p className="muted">
              This panel shows tool order and short reasoning summaries, not raw hidden chain-of-thought.
            </p>
          </div>

          <div className="inspector-block">
            <p className="section-label">Audio</p>
            <h3>Hands-free flow</h3>
            <p className="muted">
              Use the voice button to dictate prompts. Each assistant message can also be played back aloud.
            </p>
          </div>
        </aside>
      </main>
    </div>
  );
}

function MessageCard({ message, traceVisible, onSpeak }) {
  const isAssistant = message.role === "assistant";
  const hasTrace = isAssistant && message.trace?.length;

  return (
    <article className={`message ${message.role}`}>
      <div className="message-meta">{isAssistant ? "Agent" : "You"}</div>
      <div className="message-body">{message.content}</div>

      {isAssistant ? (
        <div className="message-footer">
          <button className="ghost-button" type="button" onClick={() => onSpeak(message.content)}>
            Read aloud
          </button>
          {message.toolsUsed?.length ? (
            <div className="chip-row">
              {message.toolsUsed.map((toolName) => (
                <span key={toolName} className="chip subtle">
                  {toolName}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}

      {hasTrace && traceVisible ? (
        <div className="trace-zone">
          <div className="trace-header">
            <span>Trace</span>
            <span>{message.trace.length} step{message.trace.length > 1 ? "s" : ""}</span>
          </div>
          <div className="trace-list">
            {message.trace.map((entry, index) => (
              <TraceItem key={entry.id ?? `${entry.tool}-${index}`} entry={entry} index={index} />
            ))}
          </div>
        </div>
      ) : null}
    </article>
  );
}

function TraceItem({ entry, index }) {
  return (
    <div className="trace-item" tabIndex={0}>
      <div className="trace-index">{index + 1}</div>
      <div className="trace-copy">
        <p className="trace-title">{entry.kind === "thought" ? "Reasoning note" : entry.tool}</p>
        <p className="trace-label">{entry.label}</p>
      </div>
      <div className="trace-popover" role="note">
        <p className="trace-popover-title">{entry.tool}</p>
        <pre>{formatTraceDetail(entry)}</pre>
      </div>
    </div>
  );
}

function formatTraceDetail(entry) {
  const input = entry.input ? JSON.stringify(entry.input, null, 2) : "{}";
  const output = entry.output || "No output";
  return `Input\n${input}\n\nOutput\n${output}`;
}

export default App;
