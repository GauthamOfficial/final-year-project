"use client";

import { Suspense } from "react";
import { ChatPanel } from "@/components/chat/chat-panel";
import { LandmarkIdentifier } from "@/components/vision/LandmarkIdentifier";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export function GuideTabs() {
  return (
    <Tabs defaultValue="chat" className="w-full">
      <div className="container pt-8 pb-2 md:pt-10">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="chat">Ask AI Guide</TabsTrigger>
          <TabsTrigger value="vision">Identify Landmark 📷</TabsTrigger>
        </TabsList>
      </div>
      <TabsContent value="chat" className="mt-0">
        <Suspense fallback={null}>
          <ChatPanel />
        </Suspense>
      </TabsContent>
      <TabsContent value="vision" className="mt-0">
        <div className="container py-10 md:py-14">
          <LandmarkIdentifier />
        </div>
      </TabsContent>
    </Tabs>
  );
}
