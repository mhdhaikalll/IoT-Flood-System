"use client";

import { useEffect, useState, useCallback } from "react";
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
import { CloudRain, Droplets, AlertTriangle, TrendingUp, Wifi, WifiOff, RefreshCw, Activity, Circle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getHealth, getHistory, getPrediction, getAllNodes, getRiskColor, getRiskBgColor, getStatusColor } from "@/lib/api";

// Chart configurations
const rainfallChartConfig = {
    rain_sensor_value: {
        label: "Rain Intensity (%)",
        color: "#3b82f6",
    },
    piezo_value: {
        label: "Piezo Reading (%)",
        color: "#8b5cf6",
    },
};

const waterLevelChartConfig = {
    ultrasonic_value: {
        label: "Water Level (cm)",
        color: "#06b6d4",
    },
};

const riskChartConfig = {
    risk_percentage: {
        label: "Flood Risk (%)",
        color: "#ef4444",
    },
};

const AdminPage = () => {
    // State for real data
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [systemHealth, setSystemHealth] = useState(null);
    const [sensorHistory, setSensorHistory] = useState([]);
    const [prediction, setPrediction] = useState(null);
    const [nodes, setNodes] = useState([]);
    const [lastUpdated, setLastUpdated] = useState(null);

    // Fetch all data
    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            // Fetch all data in parallel
            const [healthData, historyData, predictionData, nodesData] = await Promise.all([
                getHealth(),
                getHistory(null, 100),
                getPrediction().catch(() => null), // Don't fail if no prediction
                getAllNodes(),
            ]);

            setSystemHealth(healthData);
            setSensorHistory(historyData?.data || []);
            setPrediction(predictionData);
            setNodes(nodesData);
            setLastUpdated(new Date());
        } catch (err) {
            setError("Failed to fetch data from backend. Make sure the API is running.");
            console.error("Fetch error:", err);
        } finally {
            setLoading(false);
        }
    }, []);

    // Initial fetch and auto-refresh
    useEffect(() => {
        fetchData();

        // Auto-refresh every 30 seconds
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, [fetchData]);

    // Process sensor history for charts
    const processChartData = () => {
        if (!sensorHistory.length) return { timeSeriesData: [], hourlyData: [] };

        // Get last 24 readings for time series
        const recentData = sensorHistory.slice(-24).map((reading, index) => {
            const timestamp = reading.timestamp ? new Date(reading.timestamp) : new Date();
            return {
                time: timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
                ultrasonic_value: parseFloat(reading.ultrasonic_value) || 0,
                rain_sensor_value: parseFloat(reading.rain_sensor_value) || 0,
                piezo_value: parseFloat(reading.piezo_value) || 0,
            };
        });

        return { timeSeriesData: recentData };
    };

    const { timeSeriesData } = processChartData();

    // Calculate summary statistics
    const calculateStats = () => {
        if (!sensorHistory.length) {
            return {
                avgRainfall: 0,
                currentWaterLevel: 0,
                avgFloodRisk: 0,
                activeNodes: 0,
                onlineNodes: 0,
            };
        }

        const recent = sensorHistory.slice(-10);
        const avgRainfall = recent.reduce((sum, r) => sum + (parseFloat(r.rain_sensor_value) || 0), 0) / recent.length;
        const currentWaterLevel = parseFloat(sensorHistory[sensorHistory.length - 1]?.ultrasonic_value) || 0;

        return {
            avgRainfall: avgRainfall.toFixed(1),
            currentWaterLevel: currentWaterLevel.toFixed(1),
            avgFloodRisk: prediction?.risk_percentage?.toFixed(1) || 0,
            activeNodes: nodes.summary?.total || 0,
            onlineNodes: nodes.summary?.online || 0,
        };
    };

    const stats = calculateStats();

    // Get risk level styling
    const getRiskBadge = (risk) => {
        const variants = {
            low: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
            moderate: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100",
            high: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-100",
            critical: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100",
        };
        return variants[risk?.toLowerCase()] || variants.low;
    };

    if (loading && !sensorHistory.length) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="flex flex-col items-center gap-4">
                    <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
                    <p className="text-muted-foreground">Loading dashboard data...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Admin Dashboard</h1>
                    <p className="text-muted-foreground">
                        Real-time flood monitoring and AI predictions
                    </p>
                </div>
                <div className="flex items-center gap-4">
                    {lastUpdated && (
                        <span className="text-sm text-muted-foreground">
                            Updated: {lastUpdated.toLocaleTimeString()}
                        </span>
                    )}
                    <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
                        <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                    </Button>
                </div>
            </div>

            {/* Error Alert */}
            {error && (
                <Card className="border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950">
                    <CardContent className="flex items-center gap-2 py-4">
                        <WifiOff className="h-5 w-5 text-red-500" />
                        <span className="text-red-700 dark:text-red-300">{error}</span>
                    </CardContent>
                </Card>
            )}

            {/* System Status */}
            <Card className={systemHealth ? "border-green-200 dark:border-green-900" : "border-red-200 dark:border-red-900"}>
                <CardContent className="flex items-center justify-between py-4">
                    <div className="flex items-center gap-2">
                        {systemHealth ? (
                            <Wifi className="h-5 w-5 text-green-500" />
                        ) : (
                            <WifiOff className="h-5 w-5 text-red-500" />
                        )}
                        <span className="font-medium">
                            Backend: {systemHealth ? "Connected" : "Disconnected"}
                        </span>
                    </div>
                    {systemHealth && (
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <span>API: {systemHealth.services?.api || "unknown"}</span>
                            <span>Database: {systemHealth.services?.google_sheets || "unknown"}</span>
                            <span>AI: {systemHealth.services?.llm || "unknown"}</span>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* AI Prediction Card */}
            {prediction && (
                <Card className={getRiskBgColor(prediction.flood_risk)}>
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <CardTitle className="flex items-center gap-2">
                                <Activity className="h-5 w-5" />
                                AI Flood Prediction
                            </CardTitle>
                            <Badge className={getRiskBadge(prediction.flood_risk)}>
                                {prediction.flood_risk?.toUpperCase()} RISK
                            </Badge>
                        </div>
                        <CardDescription>{prediction.prediction_summary}</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                <div>
                                    <span className="text-muted-foreground">Water Level:</span>
                                    <p className="font-semibold">{prediction.current_water_level?.toFixed(1)} cm</p>
                                </div>
                                <div>
                                    <span className="text-muted-foreground">Rain Intensity:</span>
                                    <p className="font-semibold capitalize">{prediction.current_rain_intensity}</p>
                                </div>
                                <div>
                                    <span className="text-muted-foreground">Risk Percentage:</span>
                                    <p className="font-semibold">{prediction.risk_percentage?.toFixed(1)}%</p>
                                </div>
                                <div>
                                    <span className="text-muted-foreground">Raining:</span>
                                    <p className="font-semibold">{prediction.is_raining ? "Yes" : "No"}</p>
                                </div>
                            </div>
                            <div className="p-4 bg-background/50 rounded-lg">
                                <h4 className="font-medium mb-2">AI Analysis:</h4>
                                <p className="text-sm text-muted-foreground">{prediction.ai_analysis}</p>
                            </div>
                            {prediction.recommended_actions?.length > 0 && (
                                <div>
                                    <h4 className="font-medium mb-2">Recommended Actions:</h4>
                                    <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                                        {prediction.recommended_actions.slice(0, 3).map((action, i) => (
                                            <li key={i}>{action}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Summary Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">
                            Rain Intensity
                        </CardTitle>
                        <CloudRain className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.avgRainfall}%</div>
                        <p className="text-xs text-muted-foreground">
                            Average of last 10 readings
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">
                            Flood Risk
                        </CardTitle>
                        <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className={`text-2xl font-bold ${getRiskColor(prediction?.flood_risk)}`}>
                            {stats.avgFloodRisk}%
                        </div>
                        <p className="text-xs text-muted-foreground">
                            {prediction?.flood_risk || "No prediction"} risk level
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">
                            Active Nodes
                        </CardTitle>
                        <Wifi className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            <span className="text-green-600 dark:text-green-400">{stats.onlineNodes}</span>
                            <span className="text-muted-foreground text-lg"> / {stats.activeNodes}</span>
                        </div>
                        <p className="text-xs text-muted-foreground">
                            Online / Total nodes
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">
                            Water Level
                        </CardTitle>
                        <TrendingUp className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.currentWaterLevel} cm</div>
                        <p className="text-xs text-muted-foreground">
                            Latest sensor reading
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Charts */}
            <div className="grid gap-4 md:grid-cols-2">
                {/* Water Level Chart */}
                <Card>
                    <CardHeader>
                        <CardTitle>Water Level Over Time</CardTitle>
                        <CardDescription>
                            Real-time water level readings from sensors
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {timeSeriesData.length > 0 ? (
                            <ChartContainer config={waterLevelChartConfig} className="h-[300px] w-full">
                                <AreaChart data={timeSeriesData}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="time" />
                                    <YAxis />
                                    <ChartTooltip content={<ChartTooltipContent />} />
                                    <Area
                                        type="monotone"
                                        dataKey="ultrasonic_value"
                                        stroke="var(--color-ultrasonic_value)"
                                        fill="var(--color-ultrasonic_value)"
                                        fillOpacity={0.3}
                                    />
                                </AreaChart>
                            </ChartContainer>
                        ) : (
                            <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                                No sensor data available
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Rain Intensity Chart */}
                <Card>
                    <CardHeader>
                        <CardTitle>Rain Intensity</CardTitle>
                        <CardDescription>
                            Rainfall detection from sensors
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {timeSeriesData.length > 0 ? (
                            <ChartContainer config={rainfallChartConfig} className="h-[300px] w-full">
                                <LineChart data={timeSeriesData}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="time" />
                                    <YAxis domain={[0, 100]} />
                                    <ChartTooltip content={<ChartTooltipContent />} />
                                    <ChartLegend content={<ChartLegendContent />} />
                                    <Line
                                        type="monotone"
                                        dataKey="rain_sensor_value"
                                        stroke="var(--color-rain_sensor_value)"
                                        strokeWidth={2}
                                        dot={false}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="piezo_value"
                                        stroke="var(--color-piezo_value)"
                                        strokeWidth={2}
                                        dot={false}
                                    />
                                </LineChart>
                            </ChartContainer>
                        ) : (
                            <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                                No sensor data available
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* System Health Summary */}
            {nodes.summary && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Activity className="h-5 w-5" />
                            System Health Overview
                        </CardTitle>
                        <CardDescription>Real-time status of all IoT sensor nodes</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                            <div className="flex items-center gap-3 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
                                <Circle className="h-3 w-3 fill-green-500 text-green-500" />
                                <div>
                                    <p className="text-2xl font-bold text-green-700 dark:text-green-400">{nodes.summary.online}</p>
                                    <p className="text-xs text-green-600 dark:text-green-500">Online</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-3 p-3 rounded-lg bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800">
                                <Circle className="h-3 w-3 fill-yellow-500 text-yellow-500" />
                                <div>
                                    <p className="text-2xl font-bold text-yellow-700 dark:text-yellow-400">{nodes.summary.idle}</p>
                                    <p className="text-xs text-yellow-600 dark:text-yellow-500">Idle</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-3 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
                                <Circle className="h-3 w-3 fill-red-500 text-red-500" />
                                <div>
                                    <p className="text-2xl font-bold text-red-700 dark:text-red-400">{nodes.summary.offline}</p>
                                    <p className="text-xs text-red-600 dark:text-red-500">Offline</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-3 p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
                                <Wifi className="h-4 w-4 text-blue-500" />
                                <div>
                                    <p className="text-2xl font-bold text-blue-700 dark:text-blue-400">{nodes.summary.total}</p>
                                    <p className="text-xs text-blue-600 dark:text-blue-500">Total Nodes</p>
                                </div>
                            </div>
                        </div>
                        
                        {/* Nodes Table */}
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b">
                                        <th className="text-left py-2 px-4">Node ID</th>
                                        <th className="text-left py-2 px-4">Location</th>
                                        <th className="text-left py-2 px-4">Water Level</th>
                                        <th className="text-left py-2 px-4">Rain</th>
                                        <th className="text-left py-2 px-4">Flood Risk</th>
                                        <th className="text-left py-2 px-4">Last Seen</th>
                                        <th className="text-left py-2 px-4">Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {nodes.nodes?.map((node) => (
                                        <tr key={node.node_id} className="border-b hover:bg-muted/50">
                                            <td className="py-2 px-4 font-medium">{node.node_id}</td>
                                            <td className="py-2 px-4">{node.location}</td>
                                            <td className="py-2 px-4">
                                                {parseFloat(node.water_level || 0).toFixed(1)} cm
                                            </td>
                                            <td className="py-2 px-4">
                                                {parseFloat(node.rain_intensity || 0).toFixed(1)}%
                                            </td>
                                            <td className="py-2 px-4">
                                                <Badge variant="outline" className={getRiskBgColor(node.flood_risk)}>
                                                    {node.flood_risk || "Unknown"}
                                                </Badge>
                                            </td>
                                            <td className="py-2 px-4 text-muted-foreground text-xs">
                                                {node.last_seen_ago}
                                            </td>
                                            <td className="py-2 px-4">
                                                <Badge variant="outline" className={getStatusColor(node.status)}>
                                                    <Circle className={`h-2 w-2 mr-1 fill-current`} />
                                                    {node.status}
                                                </Badge>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
};

export default AdminPage;
