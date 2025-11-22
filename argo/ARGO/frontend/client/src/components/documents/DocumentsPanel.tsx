import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import {
  Upload,
  FileText,
  FileSpreadsheet,
  File,
  Trash2,
  Search,
  Filter,
  MoreVertical,
  CheckCircle2,
  Clock,
  AlertCircle,
  X
} from "lucide-react";
import { documentsAPI, DocumentInfo } from "@/lib/api";

export function DocumentsPanel() {
  const [uploadProgress, setUploadProgress] = React.useState<number>(0);
  const [isUploading, setIsUploading] = React.useState(false);
  const [uploadError, setUploadError] = React.useState<string | null>(null);
  const [searchQuery, setSearchQuery] = React.useState("");
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch documents
  const { data: documents, isLoading, error } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentsAPI.getDocuments(),
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => {
      setIsUploading(true);
      setUploadError(null);
      setUploadProgress(0);

      return documentsAPI.uploadDocument(file, (progress) => {
        setUploadProgress(progress);
      });
    },
    onSuccess: (data) => {
      toast({
        title: "Upload Successful",
        description: `${data.filename} has been processed with ${data.chunks} chunks`,
      });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setIsUploading(false);
      setUploadProgress(0);
    },
    onError: (error: any) => {
      const errorMsg = error.message || "Failed to upload file";
      setUploadError(errorMsg);
      toast({
        title: "Upload Failed",
        description: errorMsg,
        variant: "destructive",
      });
      setIsUploading(false);
      setUploadProgress(0);
    },
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file size (50MB max)
      if (file.size > 50 * 1024 * 1024) {
        toast({
          title: "File Too Large",
          description: "Maximum file size is 50MB",
          variant: "destructive",
        });
        return;
      }

      // Validate file type
      const allowedExtensions = ['pdf', 'docx', 'xlsx', 'txt', 'md', 'csv'];
      const fileExtension = file.name.split('.').pop()?.toLowerCase();

      if (!fileExtension || !allowedExtensions.includes(fileExtension)) {
        toast({
          title: "Invalid File Type",
          description: `Allowed: ${allowedExtensions.join(', ').toUpperCase()}`,
          variant: "destructive",
        });
        return;
      }

      uploadMutation.mutate(file);
    }

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    const file = event.dataTransfer.files?.[0];
    if (file) {
      const fakeEvent = {
        target: { files: [file] }
      } as unknown as React.ChangeEvent<HTMLInputElement>;
      handleFileSelect(fakeEvent);
    }
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
  };

  const getFileIcon = (type: string) => {
    switch (type) {
      case 'pdf':
        return <FileText className="w-5 h-5" />;
      case 'xlsx':
      case 'csv':
        return <FileSpreadsheet className="w-5 h-5" />;
      case 'docx':
      case 'txt':
      case 'md':
        return <FileText className="w-5 h-5" />;
      default:
        return <File className="w-5 h-5" />;
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  const filteredDocuments = documents?.filter((doc: DocumentInfo) =>
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-3">
          <Spinner className="w-8 h-8" />
          <p className="text-sm text-muted-foreground">Loading documents...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load documents. Please ensure the backend is running.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-6 h-full flex flex-col space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Project Documents</h2>
          <p className="text-xs text-muted-foreground">
            Manage and index knowledge base files ({documents?.length || 0} total)
          </p>
        </div>
        <Button
          className="bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm"
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
        >
          {isUploading ? (
            <>
              <Spinner className="w-4 h-4 mr-2" />
              Uploading...
            </>
          ) : (
            <>
              <Upload className="w-4 h-4 mr-2" />
              Upload Files
            </>
          )}
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleFileSelect}
          accept=".pdf,.docx,.xlsx,.txt,.md,.csv"
        />
      </div>

      {/* Upload Area */}
      <Card
        className="border-dashed border-2 border-border bg-secondary/20 hover:bg-secondary/40 transition-colors cursor-pointer"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onClick={() => !isUploading && fileInputRef.current?.click()}
      >
        <CardContent className="flex flex-col items-center justify-center py-10 text-center space-y-2">
          {isUploading ? (
            <>
              <Spinner className="w-12 h-12 text-primary mb-2" />
              <h3 className="text-sm font-medium">Uploading...</h3>
              <div className="w-full max-w-xs">
                <Progress value={uploadProgress} className="h-2" />
                <p className="text-xs text-muted-foreground mt-1">
                  {Math.round(uploadProgress)}% complete
                </p>
              </div>
            </>
          ) : (
            <>
              <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center mb-2">
                <Upload className="w-6 h-6 text-muted-foreground" />
              </div>
              <h3 className="text-sm font-medium">Drag and drop files here</h3>
              <p className="text-xs text-muted-foreground max-w-xs">
                Support for PDF, DOCX, XLSX, TXT, MD, CSV (Max 50MB)
              </p>
            </>
          )}
        </CardContent>
      </Card>

      {/* Upload Error */}
      {uploadError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            {uploadError}
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={() => setUploadError(null)}
            >
              <X className="h-4 w-4" />
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Filters and Search */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search documents..."
            className="pl-9 bg-card border-border focus-visible:ring-primary"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <Button variant="outline" size="icon" className="border-border bg-card">
          <Filter className="h-4 w-4 text-muted-foreground" />
        </Button>
      </div>

      {/* Documents List */}
      <ScrollArea className="flex-1 -mx-6 px-6">
        {filteredDocuments && filteredDocuments.length > 0 ? (
          <div className="space-y-3 pb-6">
            {filteredDocuments.map((doc: DocumentInfo, index: number) => (
              <div
                key={`${doc.filename}-${index}`}
                className="group flex items-center justify-between p-4 rounded-lg border border-border bg-card hover:border-primary/50 transition-all"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded bg-secondary flex items-center justify-center text-muted-foreground">
                    {getFileIcon(doc.file_type)}
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-foreground group-hover:text-primary transition-colors">
                      {doc.filename}
                    </h4>
                    <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                      <span>{formatFileSize(doc.file_size)}</span>
                      <span>•</span>
                      <span>{formatDate(doc.indexed_at)}</span>
                      <span>•</span>
                      <span>{doc.chunk_count} chunks</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 gap-1">
                    <CheckCircle2 className="w-3 h-3" /> Indexed
                  </Badge>

                  <Button
                    variant="ghost"
                    size="icon"
                    className="opacity-0 group-hover:opacity-100 transition-opacity h-8 w-8 text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground">
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
            <FileText className="w-12 h-12 mb-2 opacity-50" />
            <p className="text-sm">
              {searchQuery ? 'No documents found matching your search' : 'No documents uploaded yet'}
            </p>
            <p className="text-xs mt-1">Upload files to get started</p>
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
