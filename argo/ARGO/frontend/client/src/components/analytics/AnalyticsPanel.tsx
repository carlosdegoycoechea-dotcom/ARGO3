import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { analyticsAPI } from "@/lib/api";

export function AnalyticsPanel() {
  // Fetch analytics data
  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics'],
    queryFn: () => analyticsAPI.getAnalytics(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-3">
          <Spinner className="w-8 h-8" />
          <p className="text-sm text-muted-foreground">Loading analytics...</p>
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
            Failed to load analytics data. Please ensure the backend is running.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Calculate budget percentage
  const budget = 200.0;
  const budgetPercent = ((data?.budget_remaining || 0) / budget) * 100;

  // Format numbers
  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  return (
    <div className="p-6 space-y-6 h-full overflow-y-auto">
      <div>
        <h2 className="text-xl font-semibold tracking-tight">API Usage & Cost Analytics</h2>
        <p className="text-sm text-muted-foreground">Real-time tracking of system resources</p>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-card border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Monthly Cost</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${data?.monthly_cost.toFixed(2) || '0.00'}</div>
            <p className="text-xs text-muted-foreground">of ${budget.toFixed(2)} budget</p>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Tokens</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(data?.total_tokens || 0)}</div>
            <p className="text-xs text-muted-foreground">{data?.total_requests || 0} requests</p>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Daily Average</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${data?.daily_average_cost.toFixed(2) || '0.00'}</div>
            <p className="text-xs text-muted-foreground">~{formatNumber((data?.total_tokens || 0) / 30)} tokens</p>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Budget Remaining</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${budgetPercent > 20 ? 'text-emerald-500' : 'text-red-500'}`}>
              {budgetPercent.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">${data?.budget_remaining.toFixed(2) || '0.00'} left</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section */}
      <Tabs defaultValue="daily" className="space-y-4">
        <TabsList className="bg-muted border border-border">
          <TabsTrigger value="daily" className="data-[state=active]:bg-background">Daily Usage</TabsTrigger>
          <TabsTrigger value="project" className="data-[state=active]:bg-background">By Project</TabsTrigger>
          <TabsTrigger value="model" className="data-[state=active]:bg-background">By Model</TabsTrigger>
          <TabsTrigger value="type" className="data-[state=active]:bg-background">By Type</TabsTrigger>
        </TabsList>

        <TabsContent value="daily" className="space-y-4">
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-base">Daily Usage Trend (Last 7 Days)</CardTitle>
            </CardHeader>
            <CardContent className="pl-0">
              {data?.daily_usage && data.daily_usage.length > 0 ? (
                <div className="h-[300px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.daily_usage}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(0 0% 24%)" vertical={false} />
                      <XAxis
                        dataKey="day"
                        stroke="hsl(0 0% 60%)"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                      />
                      <YAxis
                        stroke="hsl(0 0% 60%)"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(value) => `${value/1000}k`}
                      />
                      <Tooltip
                        cursor={{ fill: 'hsl(0 0% 18%)' }}
                        contentStyle={{ backgroundColor: 'hsl(0 0% 14%)', borderColor: 'hsl(0 0% 24%)', color: 'hsl(0 0% 88%)' }}
                      />
                      <Bar dataKey="tokens" fill="hsl(229 76% 66%)" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  <p>No usage data available yet</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="project" className="space-y-4">
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-base">Cost Distribution by Project</CardTitle>
            </CardHeader>
            <CardContent>
              {data?.project_distribution && data.project_distribution.length > 0 ? (
                <div className="h-[300px] w-full flex items-center justify-center">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={data.project_distribution}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {data.project_distribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                        ))}
                      </Pie>
                      <Tooltip
                         contentStyle={{ backgroundColor: 'hsl(0 0% 14%)', borderColor: 'hsl(0 0% 24%)', color: 'hsl(0 0% 88%)' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  <p>No project distribution data available yet</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
