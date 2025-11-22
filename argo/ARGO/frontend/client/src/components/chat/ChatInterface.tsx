import React, { useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import { Send, Paperclip, Bot, User, ThumbsUp, ThumbsDown, RotateCcw, FileText, Check, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { chatAPI, Source } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  sources?: Source[];
  confidence?: number;
}

export function ChatInterface() {
  const [input, setInput] = React.useState("");
  const [messages, setMessages] = React.useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "ARGO Enterprise Platform initialized. Ready to assist with project management tasks.",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [wsConnected, setWsConnected] = React.useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const { toast } = useToast();

  // Initialize WebSocket on mount
  useEffect(() => {
    try {
      const ws = chatAPI.createWebSocket(
        (response) => {
          // Handle assistant response
          const aiMsg: Message = {
            id: Date.now().toString(),
            role: "assistant",
            content: response.message,
            timestamp: response.timestamp,
            sources: response.sources,
            confidence: response.confidence,
          };

          setMessages((prev) => [...prev, aiMsg]);
          setIsLoading(false);
        },
        (error) => {
          console.error("WebSocket error:", error);
          toast({
            title: "Connection Error",
            description: "Failed to communicate with server. Retrying...",
            variant: "destructive",
          });
          setIsLoading(false);
          setWsConnected(false);
        },
        () => {
          setWsConnected(false);
          console.log("WebSocket disconnected");
        }
      );

      ws.addEventListener('open', () => {
        setWsConnected(true);
      });

      wsRef.current = ws;

      return () => {
        ws.close();
      };
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
      toast({
        title: "Connection Failed",
        description: "Could not connect to server. Please check if backend is running.",
        variant: "destructive",
      });
    }
  }, [toast]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      // Try WebSocket first
      if (wsRef.current && wsConnected && wsRef.current.readyState === WebSocket.OPEN) {
        chatAPI.sendWebSocketMessage(wsRef.current, {
          message: userMsg.content,
          use_hyde: true,
          use_reranker: true,
          include_library: true,
        });
      } else {
        // Fallback to REST API
        console.log("Using REST API fallback");
        const response = await chatAPI.sendMessage({
          message: userMsg.content,
          use_hyde: true,
          use_reranker: true,
          include_library: true,
        });

        const aiMsg: Message = {
          id: Date.now().toString(),
          role: "assistant",
          content: response.message,
          timestamp: response.timestamp,
          sources: response.sources,
          confidence: response.confidence,
        };

        setMessages((prev) => [...prev, aiMsg]);
        setIsLoading(false);
      }
    } catch (error) {
      console.error("Chat error:", error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to send message",
        variant: "destructive",
      });

      // Add error message
      const errorMsg: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: "I apologize, but I encountered an error processing your request. Please ensure the backend server is running and try again.",
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, errorMsg]);
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border flex justify-between items-center bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-10">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">ARGO</h2>
          <p className="text-xs text-muted-foreground flex items-center gap-2">
            Project Assistant
            {wsConnected && (
              <span className="flex items-center gap-1 text-emerald-500">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                Connected
              </span>
            )}
            {!wsConnected && (
              <span className="flex items-center gap-1 text-amber-500">
                <AlertCircle className="w-3 h-3" />
                Offline
              </span>
            )}
          </p>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-8" ref={scrollRef}>
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex w-full max-w-4xl mx-auto gap-4",
              msg.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            {msg.role === "assistant" && (
              <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center shrink-0 border border-primary/20">
                <Bot className="w-5 h-5 text-primary" />
              </div>
            )}

            <div className="flex flex-col max-w-[85%] space-y-2">
              <div
                className={cn(
                  "rounded-md p-4 text-sm leading-relaxed shadow-sm",
                  msg.role === "user"
                    ? "bg-secondary border border-border text-foreground"
                    : "bg-card border border-border text-foreground"
                )}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>
                
                {/* Sources & Metadata for Assistant */}
                {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-border/50">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Sources Used</span>
                      {msg.confidence && (
                        <span className="text-[10px] px-1.5 py-0.5 bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 rounded font-medium">
                          {Math.round(msg.confidence * 100)}% CONFIDENCE
                        </span>
                      )}
                    </div>
                    <div className="space-y-1">
                      {msg.sources.map((source, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground cursor-pointer transition-colors">
                          <FileText className="w-3 h-3" />
                          <span className="flex items-center gap-2">
                            {source.source}
                            <span className="text-[10px] opacity-60">
                              (score: {(source.score * 100).toFixed(0)}%)
                            </span>
                            {source.is_library && (
                              <span className="text-[10px] px-1 py-0.5 bg-blue-500/10 text-blue-500 border border-blue-500/20 rounded">
                                LIBRARY
                              </span>
                            )}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons for Assistant */}
              {msg.role === "assistant" && (
                <div className="flex items-center gap-2 px-1">
                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground">
                    <ThumbsUp className="w-3.5 h-3.5" />
                  </Button>
                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground">
                    <ThumbsDown className="w-3.5 h-3.5" />
                  </Button>
                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground" title="Regenerate response">
                    <RotateCcw className="w-3.5 h-3.5" />
                  </Button>
                </div>
              )}
            </div>

            {msg.role === "user" && (
              <div className="w-8 h-8 rounded bg-secondary flex items-center justify-center shrink-0 border border-border">
                <User className="w-5 h-5 text-muted-foreground" />
              </div>
            )}
          </div>
        ))}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex w-full max-w-4xl mx-auto gap-4 justify-start">
            <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center shrink-0 border border-primary/20">
              <Bot className="w-5 h-5 text-primary" />
            </div>
            <div className="flex flex-col max-w-[85%] space-y-2">
              <div className="rounded-md p-4 text-sm bg-card border border-border">
                <div className="flex items-center gap-2">
                  <Spinner className="w-4 h-4" />
                  <span className="text-muted-foreground">Processing your request...</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-6 border-t border-border bg-background">
        <div className="max-w-4xl mx-auto space-y-3">
          <div className="relative group">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message ARGO..."
              className="min-h-[60px] max-h-[200px] w-full bg-card border-border focus-visible:ring-primary focus-visible:border-primary resize-none pl-4 pr-12 py-4 rounded-lg shadow-sm transition-all"
            />
            <div className="absolute bottom-3 right-3 flex items-center gap-2">
              <Button
                size="icon"
                className="h-8 w-8 bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm"
                onClick={handleSend}
                disabled={!input.trim()}
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
          
          <div className="flex justify-between items-center">
            <Button
              variant="outline"
              size="sm"
              className="h-8 text-xs text-muted-foreground hover:text-foreground border-border bg-transparent"
            >
              <Paperclip className="w-3.5 h-3.5 mr-2" />
              Attach Files
            </Button>
            
            <p className="text-[10px] text-muted-foreground/60 text-right font-mono">
              ARGO v9.0 ENTERPRISE
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
