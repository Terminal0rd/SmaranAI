/**
 * MindMap Page - Interactive Knowledge Map
 */
'use client';

import { useEffect, useState, useCallback, memo, useMemo } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import ReactFlow, {
    Node,
    Edge,
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    MarkerType,
    ReactFlowProvider,
    Handle,
    Position,
    NodeProps,
    useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';
import {
    ArrowLeft, Loader2, AlertCircle, RefreshCw, X,
    BookOpen, Target, Brain, CheckCircle, AlertTriangle,
    Circle, LayoutGrid, GitBranch, Layers, Sparkles, Star
} from 'lucide-react';
import { Button, Card, CardContent } from '@/components/ui';
import { mindmapAPI, subjectsAPI, sessionsAPI } from '@/lib/api';

type LayoutType = 'default' | 'tree' | 'radial' | 'grid';

// Layout algorithms
const calculateLayouts = {
    default: (nodes: any[]) => nodes,
    tree: (nodes: any[], edges: any[]) => {
        const levels: Map<string, number> = new Map();
        const hasIncoming = new Set(edges.map(e => e.target));
        const roots = nodes.filter(n => !hasIncoming.has(n.id));
        const queue = roots.map(r => ({ id: r.id, level: 0 }));
        while (queue.length > 0) {
            const { id, level } = queue.shift()!;
            if (levels.has(id)) continue;
            levels.set(id, level);
            edges.filter(e => e.source === id).forEach(e => queue.push({ id: e.target, level: level + 1 }));
        }
        const levelCounts: Map<number, number> = new Map();
        return nodes.map(node => {
            const level = levels.get(node.id) ?? 0;
            const count = levelCounts.get(level) ?? 0;
            levelCounts.set(level, count + 1);
            return { ...node, position: { x: count * 220, y: level * 150 } };
        });
    },
    radial: (nodes: any[]) => {
        const radius = Math.max(200, nodes.length * 30);
        return nodes.map((node, i) => {
            const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
            return { ...node, position: { x: radius * Math.cos(angle), y: radius * Math.sin(angle) } };
        });
    },
    grid: (nodes: any[]) => {
        const cols = Math.ceil(Math.sqrt(nodes.length));
        return nodes.map((node, i) => ({
            ...node, position: { x: (i % cols) * 200, y: Math.floor(i / cols) * 150 }
        }));
    }
};

// Custom Node Component
const ConceptNode = memo(({ data, selected }: NodeProps) => {
    const getStatusStyles = () => {
        switch (data.status) {
            case 'weak': return { border: 'border-red-500', bg: 'bg-red-500/10', progressColor: 'bg-red-500' };
            case 'strong': return { border: 'border-green-500', bg: 'bg-green-500/10', progressColor: 'bg-green-500' };
            default: return { border: 'border-violet-500', bg: 'bg-violet-500/10', progressColor: 'bg-violet-500' };
        }
    };

    const styles = getStatusStyles();
    const masteryPercent = Math.round((data.mastery_level || 0) * 100);

    return (
        <>
            <Handle type="target" position={Position.Top} className="!bg-slate-500 !w-2 !h-2" />
            <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                whileHover={{ scale: 1.05 }}
                className={`
                    px-4 py-3 rounded-xl border-2 min-w-[140px] max-w-[180px]
                    backdrop-blur-sm cursor-pointer transition-all duration-300
                    ${styles.border} ${styles.bg}
                    ${selected ? 'shadow-lg ring-2 ring-white/20' : 'hover:shadow-md'}
                `}
            >
                <div className="flex items-start justify-between gap-2 mb-2">
                    <p className="text-white font-medium text-sm leading-tight">{data.label}</p>
                    {data.status === 'weak' && <AlertTriangle className="w-3 h-3 text-red-400" />}
                    {data.status === 'strong' && <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" />}
                </div>
                <div className="space-y-1">
                    <div className="h-1.5 rounded-full bg-slate-700/50 overflow-hidden">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${masteryPercent}%` }}
                            transition={{ duration: 0.5 }}
                            className={`h-full rounded-full ${styles.progressColor}`}
                        />
                    </div>
                    <p className="text-[10px] text-slate-400 text-right">{masteryPercent}%</p>
                </div>
            </motion.div>
            <Handle type="source" position={Position.Bottom} className="!bg-slate-500 !w-2 !h-2" />
        </>
    );
});

ConceptNode.displayName = 'ConceptNode';
const nodeTypes = { concept: ConceptNode };

// Layout Switcher
function LayoutSwitcher({ current, onChange }: { current: LayoutType; onChange: (l: LayoutType) => void }) {
    const layouts = [
        { id: 'default', icon: Layers, label: 'Default' },
        { id: 'tree', icon: GitBranch, label: 'Tree' },
        { id: 'radial', icon: Circle, label: 'Radial' },
        { id: 'grid', icon: LayoutGrid, label: 'Grid' },
    ] as const;

    return (
        <div className="absolute top-4 left-4 z-10">
            <Card className="!bg-slate-900/90 backdrop-blur-sm border-slate-700">
                <CardContent className="p-2">
                    <p className="text-xs text-slate-400 mb-2 px-1">Layout</p>
                    <div className="flex gap-1">
                        {layouts.map(({ id, icon: Icon, label }) => (
                            <button
                                key={id}
                                onClick={() => onChange(id)}
                                className={`p-2 rounded-lg transition-all ${current === id ? 'bg-violet-500/20 text-violet-400' : 'text-slate-400 hover:text-white hover:bg-slate-800'}`}
                                title={label}
                            >
                                <Icon className="w-4 h-4" />
                            </button>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

// Legend
function Legend() {
    return (
        <div className="absolute bottom-4 left-4 z-10">
            <Card className="!bg-slate-900/90 backdrop-blur-sm border-slate-700">
                <CardContent className="p-3">
                    <p className="text-xs text-slate-400 mb-2">Mastery</p>
                    <div className="space-y-1.5">
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-green-500" />
                            <span className="text-xs text-slate-300">Strong</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-violet-500" />
                            <span className="text-xs text-slate-300">Learning</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-red-500" />
                            <span className="text-xs text-slate-300">Review</span>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

// Concept Panel
function ConceptPanel({ node, onClose, onStudy, onQuiz, loading }: any) {
    const masteryPercent = Math.round((node.mastery_level || 0) * 100);

    return (
        <motion.div
            initial={{ x: 100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 100, opacity: 0 }}
            className="absolute top-4 right-4 w-80 z-20"
        >
            <Card className="!bg-slate-900/95 backdrop-blur-md border-slate-700">
                <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-4">
                        <div>
                            <h3 className="text-lg font-semibold text-white">{node.label}</h3>
                            <span className={`text-xs px-2 py-0.5 rounded-full ${node.status === 'weak' ? 'bg-red-500/20 text-red-400' :
                                    node.status === 'strong' ? 'bg-green-500/20 text-green-400' :
                                        'bg-violet-500/20 text-violet-400'
                                }`}>
                                {node.status === 'weak' ? 'Needs Review' : node.status === 'strong' ? 'Mastered' : 'Learning'}
                            </span>
                        </div>
                        <button onClick={onClose} className="text-slate-400 hover:text-white">
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    <div className="mb-4">
                        <div className="flex justify-between text-sm mb-1">
                            <span className="text-slate-400">Mastery</span>
                            <span className="text-white font-medium">{masteryPercent}%</span>
                        </div>
                        <div className="h-2 rounded-full bg-slate-700">
                            <motion.div
                                animate={{ width: `${masteryPercent}%` }}
                                className={`h-full rounded-full ${masteryPercent >= 70 ? 'bg-green-500' : masteryPercent >= 30 ? 'bg-violet-500' : 'bg-red-500'}`}
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                        <Button variant="outline" size="sm" onClick={onStudy} disabled={loading}>
                            <BookOpen className="w-4 h-4 mr-1" />Study
                        </Button>
                        <Button size="sm" onClick={onQuiz} disabled={loading}>
                            <Target className="w-4 h-4 mr-1" />Quiz
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    );
}

// Stats Bar
function StatsBar({ nodes }: { nodes: Node[] }) {
    const stats = {
        total: nodes.length,
        strong: nodes.filter(n => n.data.status === 'strong').length,
        weak: nodes.filter(n => n.data.status === 'weak').length,
    };

    return (
        <div className="flex items-center gap-4 text-sm">
            <span className="text-slate-400">{stats.total} concepts</span>
            <span className="flex items-center gap-1 text-green-400">
                <CheckCircle className="w-3 h-3" />{stats.strong}
            </span>
            <span className="flex items-center gap-1 text-red-400">
                <AlertTriangle className="w-3 h-3" />{stats.weak}
            </span>
        </div>
    );
}

function MindMapFlow() {
    const params = useParams();
    const router = useRouter();
    const { fitView } = useReactFlow();
    const subjectId = params.subjectId as string;

    const [subject, setSubject] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);
    const [selectedNode, setSelectedNode] = useState<any>(null);
    const [layout, setLayout] = useState<LayoutType>('default');
    const [rawNodes, setRawNodes] = useState<any[]>([]);
    const [rawEdges, setRawEdges] = useState<any[]>([]);
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    // Apply layout
    useEffect(() => {
        if (rawNodes.length > 0) {
            const layoutFn = calculateLayouts[layout];
            const layoutedNodes = layoutFn(rawNodes, rawEdges);
            setNodes(layoutedNodes);
            setTimeout(() => fitView({ padding: 0.3 }), 100);
        }
    }, [layout, rawNodes, rawEdges, setNodes, fitView]);

    const fetchMindmap = useCallback(async () => {
        setLoading(true);
        try {
            const [subjectRes, mindmapRes] = await Promise.all([
                subjectsAPI.getById(subjectId),
                mindmapAPI.get(subjectId),
            ]);

            setSubject(subjectRes.data);

            const flowNodes: Node[] = (mindmapRes.data.nodes || []).map((node: any, i: number) => ({
                id: String(node.id),
                type: 'concept',
                position: { x: node.x_position ?? i * 200, y: node.y_position ?? i * 100 },
                data: {
                    label: node.label,
                    status: node.status || 'learning',
                    mastery_level: node.mastery_level || 0,
                },
            }));

            const flowEdges: Edge[] = (mindmapRes.data.edges || []).map((edge: any) => ({
                id: String(edge.id),
                source: String(edge.source_node_id),
                target: String(edge.target_node_id),
                type: 'smoothstep',
                animated: true,
                style: { stroke: '#8b5cf6', strokeWidth: 2 },
                markerEnd: { type: MarkerType.ArrowClosed, color: '#8b5cf6' },
            }));

            setRawNodes(flowNodes);
            setRawEdges(flowEdges);
            setNodes(flowNodes);
            setEdges(flowEdges);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [subjectId, setNodes, setEdges]);

    useEffect(() => { fetchMindmap(); }, [fetchMindmap]);

    const handleNodeClick = useCallback((event: any, node: Node) => {
        setSelectedNode(node.data);
    }, []);

    const handleStudy = async () => {
        if (!selectedNode) return;
        setActionLoading(true);
        try {
            const sessionsRes = await sessionsAPI.getAll(subjectId);
            if (sessionsRes.data.length > 0) {
                router.push(`/learn/${sessionsRes.data[0].id}?topic=${encodeURIComponent(selectedNode.label)}`);
            } else {
                const newSession = await sessionsAPI.create({ subject_id: subjectId, title: `${subject?.name} Session` });
                router.push(`/learn/${newSession.data.id}?topic=${encodeURIComponent(selectedNode.label)}`);
            }
        } catch { router.push('/learn'); }
        finally { setActionLoading(false); }
    };

    const handleQuiz = async () => {
        setActionLoading(true);
        try {
            const sessionsRes = await sessionsAPI.getAll(subjectId);
            if (sessionsRes.data[0]) router.push(`/quiz/${sessionsRes.data[0].id}`);
            else router.push('/learn');
        } catch { router.push('/learn'); }
        finally { setActionLoading(false); }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}>
                    <Brain className="w-12 h-12 text-violet-500" />
                </motion.div>
            </div>
        );
    }

    return (
        <div className="h-screen w-screen bg-slate-950 flex flex-col overflow-hidden">
            <header className="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 px-4 py-3 z-10 flex-shrink-0">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard')}>
                            <ArrowLeft className="w-4 h-4 mr-2" />Back
                        </Button>
                        <div className="border-l border-slate-700 pl-4 flex items-center gap-2">
                            <span className="text-2xl">{subject?.icon || '🧠'}</span>
                            <div>
                                <h1 className="text-white font-semibold">{subject?.name}</h1>
                                <p className="text-xs text-slate-400">Knowledge Map</p>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <StatsBar nodes={nodes} />
                        <Button variant="ghost" size="sm" onClick={fetchMindmap}><RefreshCw className="w-4 h-4" /></Button>
                    </div>
                </div>
            </header>

            <div style={{ width: '100%', height: 'calc(100vh - 64px)', flex: 1, position: 'relative' }}>
                {nodes.length > 0 ? (
                    <>
                        <ReactFlow
                            nodes={nodes}
                            edges={edges}
                            onNodesChange={onNodesChange}
                            onEdgesChange={onEdgesChange}
                            onNodeClick={handleNodeClick}
                            nodeTypes={nodeTypes}
                            fitView
                            minZoom={0.2}
                            maxZoom={2}
                            proOptions={{ hideAttribution: true }}
                        >
                            <Background color="#334155" gap={20} />
                            <Controls style={{ background: '#0f172a', borderRadius: '8px', border: '1px solid #334155' }} />
                            <MiniMap
                                style={{ background: '#0f172a', borderRadius: '8px' }}
                                nodeColor={n => n.data?.status === 'strong' ? '#22c55e' : n.data?.status === 'weak' ? '#ef4444' : '#8b5cf6'}
                            />
                        </ReactFlow>

                        <LayoutSwitcher current={layout} onChange={setLayout} />
                        <Legend />

                        <AnimatePresence>
                            {selectedNode && (
                                <ConceptPanel
                                    key="concept-panel"
                                    node={selectedNode}
                                    onClose={() => setSelectedNode(null)}
                                    onStudy={handleStudy}
                                    onQuiz={handleQuiz}
                                    loading={actionLoading}
                                />
                            )}
                        </AnimatePresence>
                    </>
                ) : (
                    <div className="h-full flex items-center justify-center">
                        <div className="text-center">
                            <Brain className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                            <h2 className="text-xl font-semibold text-white mb-2">No Concepts Yet</h2>
                            <p className="text-slate-400 mb-6">Start learning to build your knowledge map</p>
                            <Button onClick={() => router.push('/learn')}><Sparkles className="w-4 h-4 mr-2" />Start Learning</Button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default function MindMapPage() {
    return (
        <ReactFlowProvider>
            <MindMapFlow />
        </ReactFlowProvider>
    );
}
