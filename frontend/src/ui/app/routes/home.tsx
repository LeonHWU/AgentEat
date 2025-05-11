import type { Route } from "./+types/home";
import ChatLayout from "./chat";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Agent Eat Chatbot" },
    { name: "description", content: "Welcome to Agent Eat Chatbot" },
  ];
}

export default function Home() {
  return <ChatLayout />;
}
