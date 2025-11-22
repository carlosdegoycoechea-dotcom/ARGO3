import React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { 
  Plus, 
  Search, 
  Calendar, 
  Tag, 
  MoreHorizontal,
  Edit3
} from "lucide-react";

interface Note {
  id: string;
  title: string;
  content: string;
  tags: string[];
  date: string;
}

const MOCK_NOTES: Note[] = [
  { 
    id: "1", 
    title: "Project Requirements Analysis", 
    content: "Key findings from the initial stakeholder interviews:\n- Need for real-time collaboration features\n- Mobile accessibility is a priority\n- Integration with legacy systems required", 
    tags: ["requirements", "stakeholders"], 
    date: "2024-03-12" 
  },
  { 
    id: "2", 
    title: "Architecture Decision Record - Database", 
    content: "Decision: Use PostgreSQL for structured data and Vector DB for embeddings.\nContext: We need relational integrity for user data but semantic search capabilities for documents.", 
    tags: ["architecture", "database", "adr"], 
    date: "2024-03-10" 
  },
  { 
    id: "3", 
    title: "Sprint 1 Planning", 
    content: "Goals for Sprint 1:\n1. Setup basic infrastructure\n2. Implement authentication\n3. Create initial UI mockups", 
    tags: ["planning", "sprint-1"], 
    date: "2024-03-08" 
  },
];

export function NotesPanel() {
  const [isCreating, setIsCreating] = React.useState(false);

  return (
    <div className="flex h-full">
      {/* Sidebar List */}
      <div className="w-80 border-r border-border flex flex-col bg-card/50">
        <div className="p-4 border-b border-border space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-sm">My Notes</h2>
            <Button size="icon" variant="ghost" onClick={() => setIsCreating(true)} className="h-8 w-8">
              <Plus className="w-4 h-4" />
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <Input 
              placeholder="Search notes..." 
              className="pl-8 h-9 bg-background border-border text-xs"
            />
          </div>
        </div>
        
        <ScrollArea className="flex-1">
          <div className="flex flex-col gap-0.5 p-2">
            {MOCK_NOTES.map((note) => (
              <button 
                key={note.id}
                className="flex flex-col items-start p-3 rounded-md hover:bg-secondary/50 text-left transition-colors gap-1 group border border-transparent hover:border-border"
              >
                <span className="font-medium text-sm line-clamp-1 group-hover:text-primary transition-colors">
                  {note.title}
                </span>
                <span className="text-xs text-muted-foreground line-clamp-2">
                  {note.content}
                </span>
                <div className="flex items-center gap-2 mt-2 w-full">
                  <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {note.date}
                  </span>
                  <div className="flex gap-1 ml-auto">
                    {note.tags.slice(0, 2).map(tag => (
                      <Badge key={tag} variant="secondary" className="text-[10px] px-1 h-4 font-normal text-muted-foreground">
                        #{tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col bg-background">
        {isCreating ? (
          <div className="p-8 max-w-3xl mx-auto w-full space-y-6 animate-in fade-in slide-in-from-bottom-2">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Create New Note</h2>
              <div className="flex gap-2">
                <Button variant="ghost" onClick={() => setIsCreating(false)}>Cancel</Button>
                <Button>Save Note</Button>
              </div>
            </div>
            <Input 
              placeholder="Note Title" 
              className="text-lg font-medium border-transparent hover:border-border focus:border-primary bg-transparent px-0 rounded-none border-b h-12 focus-visible:ring-0" 
            />
            <div className="flex items-center gap-2 text-muted-foreground">
              <Tag className="w-4 h-4" />
              <Input 
                placeholder="Add tags (comma separated)..." 
                className="border-none bg-transparent h-8 text-sm focus-visible:ring-0 p-0"
              />
            </div>
            <Separator />
            <Textarea 
              placeholder="Start writing..." 
              className="min-h-[400px] border-none resize-none focus-visible:ring-0 p-0 text-base leading-relaxed bg-transparent"
            />
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-muted-foreground flex-col gap-4">
            <div className="w-16 h-16 rounded-full bg-secondary/50 flex items-center justify-center">
              <Edit3 className="w-8 h-8 opacity-50" />
            </div>
            <div className="text-center">
              <h3 className="font-medium text-foreground">Select a note to view</h3>
              <p className="text-sm">Or create a new one to get started</p>
            </div>
            <Button variant="outline" onClick={() => setIsCreating(true)}>
              Create New Note
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
