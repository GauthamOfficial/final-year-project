import { Suspense } from "react";
import { ChatPanel } from "@/components/chat/chat-panel";

export const metadata = {
  title: "Travel guide · LankaGuide",
  description:
    "Get grounded, sourced answers about Sri Lanka travel, including culture, wildlife, monsoons, and train routes, from the LankaGuide assistant.",
};

export default function ChatPage() {
  return (
    <Suspense fallback={null}>
      <ChatPanel />
    </Suspense>
  );
}
