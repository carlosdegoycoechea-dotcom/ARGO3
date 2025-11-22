import React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { 
  Settings, 
  Save, 
  Globe, 
  Cpu, 
  MessageSquare, 
  LayoutTemplate, 
  HardDrive 
} from "lucide-react";

export function ProjectPanel() {
  return (
    <ScrollArea className="h-full">
      <div className="p-8 max-w-4xl mx-auto space-y-8">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Project Settings</h2>
          <p className="text-muted-foreground">Manage configuration for Project Alpha</p>
        </div>

        <div className="grid gap-6">
          {/* General Information */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <LayoutTemplate className="w-4 h-4 text-primary" />
                General Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Project Name</Label>
                  <Input defaultValue="Project Alpha" className="bg-secondary/50" />
                </div>
                <div className="space-y-2">
                  <Label>Project Type</Label>
                  <Input defaultValue="Standard" disabled className="bg-muted opacity-50" />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Textarea 
                  defaultValue="Primary implementation project for the Q3 release cycle." 
                  className="bg-secondary/50 resize-none" 
                />
              </div>
              <Button className="w-fit">Save Changes</Button>
            </CardContent>
          </Card>

          {/* RAG Configuration */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Cpu className="w-4 h-4 text-primary" />
                RAG Configuration
              </CardTitle>
              <CardDescription>Configure how AI processes and retrieves information</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="text-base">HyDE Enhancement</Label>
                  <p className="text-sm text-muted-foreground">Generate hypothetical answers to improve retrieval</p>
                </div>
                <Switch defaultChecked />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="text-base">Result Reranking</Label>
                  <p className="text-sm text-muted-foreground">Re-order search results by semantic relevance</p>
                </div>
                <Switch defaultChecked />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="text-base">Knowledge Library</Label>
                  <p className="text-sm text-muted-foreground">Include global library documents in search</p>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>

          {/* Web Search */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Globe className="w-4 h-4 text-primary" />
                Web Search
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="text-base">Enable Web Search</Label>
                  <p className="text-sm text-muted-foreground">Allow AI to search the internet for current info</p>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>

          {/* Data Sources */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <HardDrive className="w-4 h-4 text-primary" />
                Data Sources
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
               <div className="flex items-center justify-between p-4 border border-border rounded-lg bg-secondary/20">
                 <div className="flex items-center gap-3">
                   <div className="w-10 h-10 rounded bg-white flex items-center justify-center">
                     <img src="https://upload.wikimedia.org/wikipedia/commons/d/da/Google_Drive_logo_%282020%29.svg" alt="Drive" className="w-6 h-6" />
                   </div>
                   <div>
                     <div className="font-medium">Google Drive Sync</div>
                     <div className="text-xs text-muted-foreground">Not connected</div>
                   </div>
                 </div>
                 <Button variant="outline" size="sm">Connect</Button>
               </div>
            </CardContent>
          </Card>

          {/* Danger Zone */}
          <Card className="border-destructive/50 bg-destructive/5">
            <CardHeader>
              <CardTitle className="text-base text-destructive">Danger Zone</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <div className="font-medium text-destructive">Delete Project</div>
                  <div className="text-sm text-muted-foreground">Permanently delete this project and all its data</div>
                </div>
                <Button variant="destructive" size="sm">Delete Project</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </ScrollArea>
  );
}
