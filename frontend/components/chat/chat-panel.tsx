"use client";

import { useEffect, useReducer, useRef, useState } from "react";
import { Send, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectItem } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { api, toApiError } from "@/lib/api";
import { cn } from "@/lib/utils";

// ─────────────────────────── Types ──────────────────────────────────────
type Source = {
  doc_id: string;
  title: string;
  relevance: number;
  attraction_id?: number | null;
  district_id?: number | null;
  category?: string | null;
};

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  pending?: boolean;
};

type Action =
  | { type: "append"; message: Message }
  | { type: "patch"; id: string; patch: Partial<Message> }
  | { type: "reset" };

function reducer(state: Message[], action: Action): Message[] {
  switch (action.type) {
    case "append":
      return [...state, action.message];
    case "patch":
      return state.map((m) => (m.id === action.id ? { ...m, ...action.patch } : m));
    case "reset":
      return [];
    default:
      return state;
  }
}

const STARTER_QUESTIONS = [
  "When is the best time to visit Sigiriya?",
  "Plan a 3-day trip to Galle and the south coast.",
  "What wildlife can I see in Yala National Park?",
  "How do I get from Colombo to Ella by train?",
];

// ─────────────────────────── Component ──────────────────────────────────
export function ChatPanel() {
  const [messages, dispatch] = useReducer(reducer, []);
  const [input, setInput] = useState("");
  const [language, setLanguage] = useState<"en" | "si" | "ta">("en");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const stored = localStorage.getItem("lankaguide.chat_session_id");
    if (stored) setSessionId(Number(stored));
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  async function send(text: string) {
    if (!text.trim() || busy) return;
    setError(null);
    const userId = `u-${crypto.randomUUID()}`;
    const assistantId = `a-${crypto.randomUUID()}`;
    dispatch({ type: "append", message: { id: userId, role: "user", content: text } });
    dispatch({
      type: "append",
      message: { id: assistantId, role: "assistant", content: "", pending: true },
    });
    setInput("");
    setBusy(true);
    try {
      const { data } = await api.post("/api/v1/chat/message/", {
        message: text,
        language,
        session_id: sessionId,
      });
      if (data.session_id && data.session_id !== sessionId) {
        setSessionId(data.session_id);
        localStorage.setItem("lankaguide.chat_session_id", String(data.session_id));
      }
      dispatch({
        type: "patch",
        id: assistantId,
        patch: {
          content: data.response,
          sources: data.sources ?? [],
          pending: false,
        },
      });
    } catch (err) {
      const apiErr = toApiError(err);
      dispatch({
        type: "patch",
        id: assistantId,
        patch: {
          pending: false,
          content:
            "Sorry — the AI service is unavailable right now. " +
            "Try again in a moment.",
        },
      });
      setError(apiErr.message);
    } finally {
      setBusy(false);
    }
  }

  function newSession() {
    setSessionId(null);
    localStorage.removeItem("lankaguide.chat_session_id");
    dispatch({ type: "reset" });
  }

  return (
    <div className="flex h-full flex-col bg-background">
      {/* Header */}
      <header className="flex h-16 shrink-0 items-center justify-between border-b px-6">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-accent" />
          <div>
            <h1 className="text-base font-semibold leading-none">Ask LankaGuide</h1>
            <p className="text-xs text-muted-foreground">
              RAG-grounded answers from a curated Sri Lanka knowledge base.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Select
            value={language}
            onValueChange={(v) => setLanguage(v as "en" | "si" | "ta")}
            className="h-8 w-32"
          >
            <SelectItem value="en">English</SelectItem>
            <SelectItem value="si">සිංහල</SelectItem>
            <SelectItem value="ta">தமிழ்</SelectItem>
          </Select>
          <Button variant="outline" size="sm" onClick={newSession}>
            New chat
          </Button>
        </div>
      </header>

      {/* Messages */}
      <ScrollArea ref={scrollRef} className="flex-1 px-6 py-6">
        {messages.length === 0 && <EmptyState onPick={send} />}
        <div className="mx-auto flex max-w-3xl flex-col gap-6 pb-4">
          {messages.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}
        </div>
      </ScrollArea>

      {/* Composer */}
      <div className="border-t bg-card/40 px-6 py-4">
        <div className="mx-auto max-w-3xl">
          {error && (
            <p className="mb-2 text-xs text-destructive">{error}</p>
          )}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
            className="flex items-end gap-2"
          >
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send(input);
                }
              }}
              placeholder="Ask anything about Sri Lanka travel — Enter to send, Shift+Enter for newline."
              rows={2}
              className="resize-none"
              disabled={busy}
            />
            <Button type="submit" disabled={busy || !input.trim()} size="icon">
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────── Sub-components ─────────────────────────────
function EmptyState({ onPick }: { onPick: (q: string) => void }) {
  return (
    <div className="mx-auto flex max-w-3xl flex-col items-center justify-center gap-6 py-24 text-center">
      <div className="rounded-full bg-primary/10 p-3">
        <Sparkles className="h-6 w-6 text-primary" />
      </div>
      <div className="space-y-1">
        <h2 className="text-xl font-semibold">Your AI travel companion for Sri Lanka</h2>
        <p className="max-w-md text-sm text-muted-foreground">
          Ask about cultural sites, beaches, wildlife, or get help planning a trip.
          Every answer is grounded in verified, curated local knowledge.
        </p>
      </div>
      <div className="grid w-full max-w-xl grid-cols-1 gap-2 sm:grid-cols-2">
        {STARTER_QUESTIONS.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => onPick(q)}
            className="rounded-lg border bg-card px-4 py-3 text-left text-sm text-muted-foreground transition-colors hover:border-primary hover:bg-primary/5 hover:text-foreground"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex gap-3", isUser && "flex-row-reverse")}>
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold",
          isUser ? "bg-primary text-primary-foreground" : "bg-accent text-accent-foreground"
        )}
      >
        {isUser ? "You" : "AI"}
      </div>
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
          isUser ? "bg-primary text-primary-foreground" : "bg-muted text-foreground"
        )}
      >
        {message.pending ? (
          <span className="inline-flex gap-1">
            <Dot delay="0ms" /> <Dot delay="120ms" /> <Dot delay="240ms" />
          </span>
        ) : isUser ? (
          message.content
        ) : (
          <div className="space-y-2 [&_a]:text-primary [&_a]:underline [&_code]:rounded [&_code]:bg-background/60 [&_code]:px-1 [&_code]:py-0.5 [&_h1]:text-base [&_h1]:font-semibold [&_h2]:text-sm [&_h2]:font-semibold [&_li]:list-disc [&_li]:ml-5 [&_p]:leading-relaxed [&_strong]:font-semibold">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}

        {message.sources && message.sources.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            {message.sources.slice(0, 4).map((s) => (
              <Badge
                key={s.doc_id}
                variant="outline"
                title={`Relevance ${Math.round(s.relevance * 100)}%`}
                className="text-[10px] font-medium"
              >
                {s.title} · {Math.round(s.relevance * 100)}%
              </Badge>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function Dot({ delay }: { delay: string }) {
  return (
    <span
      className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-current opacity-60"
      style={{ animationDelay: delay }}
    />
  );
}
