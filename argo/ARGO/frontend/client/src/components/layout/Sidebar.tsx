import React from "react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { 
  Plus, 
  Save, 
  Download, 
  MessageSquare, 
  Edit2, 
  Trash2, 
  Settings, 
  HardDrive, 
  FileText,
  Activity,
  Search
} from "lucide-react";

export function Sidebar() {
  const [activeProject, setActiveProject] = React.useState("Project Alpha");

  return (
    <div className="w-80 h-screen border-r border-border bg-sidebar text-sidebar-foreground flex flex-col font-sans">
      <div className="p-5 flex flex-col gap-1">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight text-foreground">ARGO</h1>
          <Badge variant="outline" className="text-[10px] border-border text-muted-foreground bg-sidebar-accent">ENTERPRISE</Badge>
        </div>
        <p className="text-[10px] text-muted-foreground uppercase tracking-widest">PMO Platform</p>
      </div>
      
      <Separator className="bg-border/50" />

      <ScrollArea className="flex-1 px-4 py-4">
        <div className="space-y-8">
          {/* Projects Section */}
          <div>
            <div className="flex items-center justify-between mb-3 px-1">
              <h2 className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider">Projects</h2>
              <Settings className="w-3 h-3 text-muted-foreground hover:text-foreground cursor-pointer" />
            </div>
            
            <Select value={activeProject} onValueChange={setActiveProject}>
              <SelectTrigger className="w-full bg-sidebar-accent border-sidebar-border text-sidebar-foreground h-9 text-sm focus:ring-0 focus:ring-offset-0">
                <SelectValue placeholder="Select Project" />
              </SelectTrigger>
              <SelectContent className="bg-sidebar-accent border-sidebar-border text-sidebar-foreground">
                <SelectItem value="Project Alpha">Project Alpha</SelectItem>
                <SelectItem value="Project Beta">Project Beta</SelectItem>
                <SelectItem value="Project Gamma">Project Gamma</SelectItem>
              </SelectContent>
            </Select>

            <Accordion type="single" collapsible className="mt-3">
              <AccordionItem value="new-project" className="border-none">
                <AccordionTrigger className="text-xs py-2 hover:no-underline text-muted-foreground hover:text-primary justify-start gap-2 px-1">
                  <Plus className="w-3 h-3" />
                  Create New Project
                </AccordionTrigger>
                <AccordionContent>
                  <div className="space-y-3 pt-2 pl-1 pr-1">
                    <Input 
                      placeholder="Project Name" 
                      className="bg-sidebar-accent border-sidebar-border h-8 text-xs" 
                    />
                    <Select defaultValue="standard">
                      <SelectTrigger className="w-full bg-sidebar-accent border-sidebar-border h-8 text-xs">
                        <SelectValue placeholder="Type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="standard">Standard</SelectItem>
                        <SelectItem value="construction">Construction</SelectItem>
                        <SelectItem value="it">IT</SelectItem>
                        <SelectItem value="research">Research</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button size="sm" className="w-full bg-primary hover:bg-primary/90 text-primary-foreground h-7 text-xs font-medium">
                      Create
                    </Button>
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </div>

          {/* Current Project Stats */}
          <div>
             <div className="flex items-center justify-between mb-3 px-1">
              <h2 className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider">Active Project</h2>
              <Activity className="w-3 h-3 text-muted-foreground" />
            </div>
            <div className="bg-sidebar-accent/50 rounded-md p-3 space-y-2 border border-sidebar-border">
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Type</span>
                <span className="font-medium text-foreground">Standard</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Status</span>
                <span className="text-emerald-500 font-medium flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                  Active
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Docs</span>
                <span className="font-medium text-foreground">142</span>
              </div>
            </div>
          </div>

          {/* Conversations Section */}
          <div>
             <div className="flex items-center justify-between mb-3 px-1">
              <h2 className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider">Conversations</h2>
            </div>
            
            <div className="grid grid-cols-3 gap-1 mb-3">
              <Button variant="outline" size="sm" className="bg-sidebar-accent border-sidebar-border hover:bg-sidebar-accent/80 h-7 text-xs px-0 gap-1 text-muted-foreground hover:text-foreground">
                <Plus className="h-3 w-3" /> New
              </Button>
              <Button variant="outline" size="sm" className="bg-sidebar-accent border-sidebar-border hover:bg-sidebar-accent/80 h-7 text-xs px-0 gap-1 text-muted-foreground hover:text-foreground">
                <Save className="h-3 w-3" /> Save
              </Button>
              <Button variant="outline" size="sm" className="bg-sidebar-accent border-sidebar-border hover:bg-sidebar-accent/80 h-7 text-xs px-0 gap-1 text-muted-foreground hover:text-foreground">
                <Download className="h-3 w-3" /> Export
              </Button>
            </div>

            <Accordion type="single" collapsible defaultValue="recent">
              <AccordionItem value="recent" className="border-none">
                <AccordionTrigger className="text-xs py-2 hover:no-underline text-muted-foreground hover:text-foreground font-medium justify-between px-1">
                  <span>Recent History</span>
                  <span className="text-[10px] bg-sidebar-accent px-1.5 rounded border border-sidebar-border">5</span>
                </AccordionTrigger>
                <AccordionContent>
                  <div className="space-y-0.5 mt-1">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <div key={i} className="group flex items-center justify-between p-2 hover:bg-sidebar-accent rounded-sm cursor-pointer transition-colors text-xs border border-transparent hover:border-sidebar-border">
                        <div className="flex items-center gap-2 overflow-hidden">
                          <MessageSquare className="h-3 w-3 text-muted-foreground shrink-0" />
                          <span className="truncate text-muted-foreground group-hover:text-foreground transition-colors">
                            Session {20240310}_{i}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </div>

          {/* Notes Section */}
          <div>
             <div className="flex items-center justify-between mb-3 px-1">
              <h2 className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider">Notes</h2>
              <FileText className="w-3 h-3 text-muted-foreground" />
            </div>
            <div className="text-xs text-muted-foreground italic px-1">No active notes</div>
          </div>
          
          {/* Drive Sync */}
          <div>
             <div className="flex items-center justify-between mb-3 px-1">
              <h2 className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider">Data Sources</h2>
            </div>
            <Button variant="outline" size="sm" className="w-full justify-start bg-sidebar-accent border-sidebar-border hover:bg-sidebar-accent/80 h-8 text-xs text-muted-foreground hover:text-foreground">
               <HardDrive className="h-3 w-3 mr-2" />
               Google Drive Sync
            </Button>
          </div>
        </div>
      </ScrollArea>
      
      <div className="p-4 border-t border-border bg-sidebar-accent/30">
        <div className="flex items-center gap-3">
           <div className="w-8 h-8 rounded bg-primary/20 flex items-center justify-center border border-primary/30 text-primary font-bold text-xs">
             JS
           </div>
           <div className="flex flex-col">
             <span className="text-xs font-medium text-foreground">John Smith</span>
             <span className="text-[10px] text-muted-foreground">Project Manager</span>
           </div>
        </div>
      </div>
    </div>
  );
}
