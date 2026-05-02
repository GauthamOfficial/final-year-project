/**
 * Chat page — implementation lands in Prompt 5A. This file ships now so the
 * sidebar nav + route group resolves immediately after Prompt 1B.
 */
import { ChatPanel } from "@/components/chat/chat-panel";

export const metadata = { title: "AI Chat · LankaGuide" };

export default function ChatPage() {
  return (
    <div className="flex h-screen flex-col">
      <ChatPanel />
    </div>
  );
}
