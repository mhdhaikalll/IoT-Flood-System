"use client";

import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import {
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
    ChartLegend,
    ChartLegendContent,
} from "@/components/ui/chart";
import {
    LineChart,
    Line,
    BarChart,
    Bar,
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    ResponsiveContainer,
} from "recharts";
import { CloudRain, Droplets, AlertTriangle, TrendingUp } from "lucide-react";

// Dummy data for rainfall over the past 7 days
const rainfallData = [
    { day: "Mon", rainfall: 12, floodRisk: 15 },
    { day: "Tue", rainfall: 25, floodRisk: 30 },
    { day: "Wed", rainfall: 45, floodRisk: 55 },
    { day: "Thu", rainfall: 38, floodRisk: 45 },
    { day: "Fri", rainfall: 52, floodRisk: 65 },
    { day: "Sat", rainfall: 30, floodRisk: 35 },
    { day: "Sun", rainfall: 18, floodRisk: 20 },
];

// Dummy data for monthly flood incidents
const floodIncidentsData = [
    { month: "Jan", incidents: 2, severity: 3 },
    { month: "Feb", incidents: 1, severity: 2 },
    { month: "Mar", incidents: 4, severity: 5 },
    { month: "Apr", incidents: 6, severity: 7 },
    { month: "May", incidents: 8, severity: 9 },
    { month: "Jun", incidents: 5, severity: 6 },
];

// Dummy data for water levels
const waterLevelData = [
    { time: "00:00", level: 2.1 },
    { time: "04:00", level: 2.3 },
    { time: "08:00", level: 2.8 },
    { time: "12:00", level: 3.2 },
    { time: "16:00", level: 3.5 },
    { time: "20:00", level: 3.1 },
    { time: "24:00", level: 2.7 },
];

// Dummy data for regional flood risk
const regionalData = [
    { region: "North", riskLevel: 75 },
    { region: "South", riskLevel: 45 },
    { region: "East", riskLevel: 60 },
    { region: "West", riskLevel: 30 },
    { region: "Central", riskLevel: 85 },
];

const rainfallChartConfig = {
    rainfall: {
        label: "Rainfall (mm)",
        color: "#3b82f6", // Blue
    },
    floodRisk: {
        label: "Flood Risk (%)",
        color: "#ef4444", // Red
    },
};

const floodIncidentsChartConfig = {
    incidents: {
        label: "Incidents",
        color: "#8b5cf6", // Purple
    },
    severity: {
        label: "Severity",
        color: "#f97316", // Orange
    },
};

const waterLevelChartConfig = {
    level: {
        label: "Water Level (m)",
        color: "#06b6d4", // Cyan
    },
};

const regionalChartConfig = {
    riskLevel: {
        label: "Risk Level (%)",
        color: "#10b981", // Emerald
    },
};

const AdminPage = () => {
    // Summary stats
    const totalRainfall = rainfallData.reduce((acc, curr) => acc + curr.rainfall, 0);
    const avgFloodRisk = Math.round(
        rainfallData.reduce((acc, curr) => acc + curr.floodRisk, 0) / rainfallData.length
    );
    const totalIncidents = floodIncidentsData.reduce((acc, curr) => acc + curr.incidents, 0);
    const currentWaterLevel = waterLevelData[waterLevelData.length - 2].level;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold">Admin Dashboard</h1>
                <p className="text-muted-foreground">
                    Rain and flood monitoring overview
                </p>
            </div>

            {/* Summary Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">
                            Weekly Rainfall
                        </CardTitle>
                        <CloudRain className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{totalRainfall} mm</div>
                        <p className="text-xs text-muted-foreground">
                            +12% from last week
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">
                            Avg Flood Risk
                        </CardTitle>
                        <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{avgFloodRisk}%</div>
                        <p className="text-xs text-muted-foreground">
                            Moderate risk level
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">
                            Flood Incidents (YTD)
                        </CardTitle>
                        <Droplets className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{totalIncidents}</div>
                        <p className="text-xs text-muted-foreground">
                            Across all regions
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">
                            Current Water Level
                        </CardTitle>
                        <TrendingUp className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{currentWaterLevel} m</div>
                        <p className="text-xs text-muted-foreground">
                            Main river station
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Charts Row 1 */}
            <div className="grid gap-4 md:grid-cols-2">
                {/* Rainfall & Flood Risk Chart */}
                <Card>
                    <CardHeader>
                        <CardTitle>Rainfall & Flood Risk</CardTitle>
                        <CardDescription>
                            Daily rainfall and corresponding flood risk percentage
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <ChartContainer config={rainfallChartConfig} className="h-[300px] w-full">
                            <LineChart data={rainfallData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="day" />
                                <YAxis />
                                <ChartTooltip content={<ChartTooltipContent />} />
                                <ChartLegend content={<ChartLegendContent />} />
                                <Line
                                    type="monotone"
                                    dataKey="rainfall"
                                    stroke="var(--color-rainfall)"
                                    strokeWidth={2}
                                    dot={{ r: 4 }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="floodRisk"
                                    stroke="var(--color-floodRisk)"
                                    strokeWidth={2}
                                    dot={{ r: 4 }}
                                />
                            </LineChart>
                        </ChartContainer>
                    </CardContent>
                </Card>

                {/* Monthly Flood Incidents */}
                <Card>
                    <CardHeader>
                        <CardTitle>Monthly Flood Incidents</CardTitle>
                        <CardDescription>
                            Number of incidents and severity score by month
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <ChartContainer config={floodIncidentsChartConfig} className="h-[300px] w-full">
                            <BarChart data={floodIncidentsData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="month" />
                                <YAxis />
                                <ChartTooltip content={<ChartTooltipContent />} />
                                <ChartLegend content={<ChartLegendContent />} />
                                <Bar
                                    dataKey="incidents"
                                    fill="var(--color-incidents)"
                                    radius={[4, 4, 0, 0]}
                                />
                                <Bar
                                    dataKey="severity"
                                    fill="var(--color-severity)"
                                    radius={[4, 4, 0, 0]}
                                />
                            </BarChart>
                        </ChartContainer>
                    </CardContent>
                </Card>
            </div>

            {/* Charts Row 2 */}
            <div className="grid gap-4 md:grid-cols-2">
                {/* Water Level Over Time */}
                <Card>
                    <CardHeader>
                        <CardTitle>Water Level Today</CardTitle>
                        <CardDescription>
                            Hourly water level readings from main station
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <ChartContainer config={waterLevelChartConfig} className="h-[300px] w-full">
                            <AreaChart data={waterLevelData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="time" />
                                <YAxis domain={[0, 5]} />
                                <ChartTooltip content={<ChartTooltipContent />} />
                                <Area
                                    type="monotone"
                                    dataKey="level"
                                    stroke="var(--color-level)"
                                    fill="var(--color-level)"
                                    fillOpacity={0.3}
                                />
                            </AreaChart>
                        </ChartContainer>
                    </CardContent>
                </Card>

                {/* Regional Flood Risk */}
                <Card>
                    <CardHeader>
                        <CardTitle>Regional Flood Risk</CardTitle>
                        <CardDescription>
                            Current flood risk levels by region
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <ChartContainer config={regionalChartConfig} className="h-[300px] w-full">
                            <BarChart data={regionalData} layout="vertical">
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis type="number" domain={[0, 100]} />
                                <YAxis dataKey="region" type="category" width={60} />
                                <ChartTooltip content={<ChartTooltipContent />} />
                                <Bar
                                    dataKey="riskLevel"
                                    fill="var(--color-riskLevel)"
                                    radius={[0, 4, 4, 0]}
                                />
                            </BarChart>
                        </ChartContainer>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default AdminPage;
