import React from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { AnalyticsPanel } from "@/components/analytics/AnalyticsPanel";
import { DocumentsPanel } from "@/components/documents/DocumentsPanel";
import { NotesPanel } from "@/components/notes/NotesPanel";
import { ProjectPanel } from "@/components/project/ProjectPanel";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LayoutDashboard, MessageSquare, FileText, Settings, Briefcase } from "lucide-react";

export default function Dashboard() {
  const [activeTab, setActiveTab] = React.useState("chat");

  return (
    <MainLayout>
      <div className="h-full flex flex-col">
        {/* Top Navigation Bar for Tabs - Professional Style */}
        <div className="border-b border-border bg-background px-6">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <div className="flex items-center justify-between">
              <TabsList className="h-12 bg-transparent p-0 space-x-6">
                <TabsTrigger 
                  value="chat" 
                  className="h-12 rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none px-0 text-muted-foreground data-[state=active]:text-foreground transition-none"
                >
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <MessageSquare className="w-4 h-4" />
                    Chat
                  </div>
                </TabsTrigger>
                <TabsTrigger 
                  value="documents" 
                  className="h-12 rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none px-0 text-muted-foreground data-[state=active]:text-foreground transition-none"
                >
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <FileText className="w-4 h-4" />
                    Documents
                  </div>
                </TabsTrigger>
                <TabsTrigger 
                  value="analytics" 
                  className="h-12 rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none px-0 text-muted-foreground data-[state=active]:text-foreground transition-none"
                >
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <LayoutDashboard className="w-4 h-4" />
                    Analytics
                  </div>
                </TabsTrigger>
                 <TabsTrigger 
                  value="notes" 
                  className="h-12 rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none px-0 text-muted-foreground data-[state=active]:text-foreground transition-none"
                >
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <Briefcase className="w-4 h-4" />
                    Conversations & Notes
                  </div>
                </TabsTrigger>
                <TabsTrigger 
                  value="project" 
                  className="h-12 rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none px-0 text-muted-foreground data-[state=active]:text-foreground transition-none"
                >
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <Settings className="w-4 h-4" />
                    Project
                  </div>
                </TabsTrigger>
              </TabsList>
            </div>
          </Tabs>
        </div>

        <div className="flex-1 overflow-hidden relative bg-background">
          {activeTab === "chat" && (
            <div className="absolute inset-0 animate-in fade-in duration-200">
              <ChatInterface />
            </div>
          )}
          
          {activeTab === "documents" && (
            <div className="absolute inset-0 animate-in fade-in duration-200">
              <DocumentsPanel />
            </div>
          )}

          {activeTab === "analytics" && (
            <div className="absolute inset-0 animate-in fade-in duration-200">
              <AnalyticsPanel />
            </div>
          )}

          {activeTab === "notes" && (
            <div className="absolute inset-0 animate-in fade-in duration-200">
              <NotesPanel />
            </div>
          )}

          {activeTab === "project" && (
            <div className="absolute inset-0 animate-in fade-in duration-200">
              <ProjectPanel />
            </div>
          )}
        </div>
      </div>
    </MainLayout>
  );
}
