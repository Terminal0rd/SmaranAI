/**
 * MindMap Page - Interactive Knowledge Map
 * Enhanced with: concept descriptions on click, quiz-colored nodes
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
    Circle, LayoutGrid, GitBranch, Layers, Sparkles, Star,
    Info, TrendingUp, XCircle
} from 'lucide-react';
import { Button, Card, CardContent } from '@/components/ui';
import { mindmapAPI, subjectsAPI, sessionsAPI, quizAPI } from '@/lib/api';

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

// Custom Node Component with quiz-aware coloring
const ConceptNode = memo(({ data, selected }: NodeProps) => {
    const getStatusStyles = () => {
        // Quiz-based coloring takes priority
        if (data.quizStatus === 'correct') {
            return { border: 'border-green-500', bg: 'bg-green-500/10', progressColor: 'bg-green-500', glow: 'shadow-green-500/20' };
        }
        if (data.quizStatus === 'wrong') {
            return { border: 'border-red-500', bg: 'bg-red-500/10', progressColor: 'bg-red-500', glow: 'shadow-red-500/20' };
        }
        // Fall back to mastery-based coloring
        switch (data.status) {
            case 'weak': return { border: 'border-red-500', bg: 'bg-red-500/10', progressColor: 'bg-red-500', glow: '' };
            case 'strong': return { border: 'border-green-500', bg: 'bg-green-500/10', progressColor: 'bg-green-500', glow: '' };
            default: return { border: 'border-violet-500', bg: 'bg-violet-500/10', progressColor: 'bg-violet-500', glow: '' };
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
                    ${styles.glow ? `shadow-lg ${styles.glow}` : ''}
                `}
            >
                <div className="flex items-start justify-between gap-2 mb-2">
                    <p className="text-white font-medium text-sm leading-tight">{data.label}</p>
                    {data.quizStatus === 'correct' && <CheckCircle className="w-3 h-3 text-green-400 flex-shrink-0" />}
                    {data.quizStatus === 'wrong' && <XCircle className="w-3 h-3 text-red-400 flex-shrink-0" />}
                    {!data.quizStatus && data.status === 'weak' && <AlertTriangle className="w-3 h-3 text-red-400 flex-shrink-0" />}
                    {!data.quizStatus && data.status === 'strong' && <Star className="w-3 h-3 text-yellow-400 fill-yellow-400 flex-shrink-0" />}
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

// Legend - updated with quiz colors
function Legend({ hasQuizData }: { hasQuizData: boolean }) {
    return (
        <div className="absolute bottom-4 left-4 z-10">
            <Card className="!bg-slate-900/90 backdrop-blur-sm border-slate-700">
                <CardContent className="p-3">
                    <p className="text-xs text-slate-400 mb-2">{hasQuizData ? 'Quiz Performance' : 'Mastery'}</p>
                    <div className="space-y-1.5">
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-green-500" />
                            <span className="text-xs text-slate-300">{hasQuizData ? 'Correct in Quiz' : 'Strong'}</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-violet-500" />
                            <span className="text-xs text-slate-300">{hasQuizData ? 'Not Quizzed' : 'Learning'}</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-red-500" />
                            <span className="text-xs text-slate-300">{hasQuizData ? 'Wrong in Quiz' : 'Needs Review'}</span>
                        </div>
                    </div>
                    {hasQuizData && (
                        <p className="text-[10px] text-slate-500 mt-2 italic">Based on your quiz results</p>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}

// Enhanced Concept Panel with description + quiz stats
function ConceptPanel({ node, nodeId, onClose, onStudy, onQuiz, loading, quizStats }: any) {
    const masteryPercent = Math.round((node.mastery_level || 0) * 100);
    const [description, setDescription] = useState<string | null>(null);
    const [descLoading, setDescLoading] = useState(false);

    // Fetch description when panel opens
    useEffect(() => {
        if (!nodeId) return;
        
        // Check if we have a cached description in node data
        if (node.description) {
            setDescription(node.description);
            return;
        }

        let cancelled = false;
        const fetchDescription = async () => {
            setDescLoading(true);
            try {
                const res = await mindmapAPI.describeNode(nodeId);
                if (!cancelled) {
                    setDescription(res.data.description);
                }
            } catch (err) {
                if (!cancelled) {
                    setDescription(`A concept in this subject. Click 'Study' to learn more.`);
                }
            } finally {
                if (!cancelled) setDescLoading(false);
            }
        };
        fetchDescription();
        return () => { cancelled = true; };
    }, [nodeId, node.description]);

    return (
        <motion.div
            initial={{ x: 100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 100, opacity: 0 }}
            className="absolute top-4 right-4 w-80 z-20"
        >
            <Card className="!bg-slate-900/95 backdrop-blur-md border-slate-700">
                <CardContent className="p-4">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                            <h3 className="text-lg font-semibold text-white">{node.label}</h3>
                            <span className={`text-xs px-2 py-0.5 rounded-full ${node.quizStatus === 'correct' ? 'bg-green-500/20 text-green-400' :
                                    node.quizStatus === 'wrong' ? 'bg-red-500/20 text-red-400' :
                                    node.status === 'weak' ? 'bg-red-500/20 text-red-400' :
                                    node.status === 'strong' ? 'bg-green-500/20 text-green-400' :
                                        'bg-violet-500/20 text-violet-400'
                                }`}>
                                {node.quizStatus === 'correct' ? '✓ Quiz Correct' :
                                 node.quizStatus === 'wrong' ? '✗ Quiz Wrong' :
                                 node.status === 'weak' ? 'Needs Review' : 
                                 node.status === 'strong' ? 'Mastered' : 'Learning'}
                            </span>
                        </div>
                        <button onClick={onClose} className="text-slate-400 hover:text-white p-1">
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Mastery Bar */}
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

                    {/* Description */}
                    <div className="mb-4 p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
                        <div className="flex items-center gap-2 mb-2">
                            <Info className="w-3.5 h-3.5 text-violet-400" />
                            <span className="text-xs font-medium text-violet-400">About this concept</span>
                        </div>
                        {descLoading ? (
                            <div className="flex items-center gap-2 py-2">
                                <Loader2 className="w-4 h-4 text-violet-400 animate-spin" />
                                <span className="text-xs text-slate-400">Generating description...</span>
                            </div>
                        ) : (
                            <p className="text-sm text-slate-300 leading-relaxed">
                                {description || 'No description available.'}
                            </p>
                        )}
                    </div>

                    {/* Quiz Stats (if available) */}
                    {quizStats && (
                        <div className="mb-4 p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
                            <div className="flex items-center gap-2 mb-2">
                                <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
                                <span className="text-xs font-medium text-amber-400">Quiz Performance</span>
                            </div>
                            <div className="flex items-center gap-4 text-sm">
                                <div className="flex items-center gap-1">
                                    <CheckCircle className="w-3.5 h-3.5 text-green-400" />
                                    <span className="text-green-400 font-medium">{quizStats.correct}</span>
                                    <span className="text-slate-500">correct</span>
                                </div>
                                <div className="flex items-center gap-1">
                                    <XCircle className="w-3.5 h-3.5 text-red-400" />
                                    <span className="text-red-400 font-medium">{quizStats.wrong}</span>
                                    <span className="text-slate-500">wrong</span>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Action Buttons */}
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
function StatsBar({ nodes, hasQuizData }: { nodes: Node[]; hasQuizData: boolean }) {
    const stats = {
        total: nodes.length,
        strong: nodes.filter(n => n.data.quizStatus === 'correct' || n.data.status === 'strong').length,
        weak: nodes.filter(n => n.data.quizStatus === 'wrong' || n.data.status === 'weak').length,
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
    const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
    const [layout, setLayout] = useState<LayoutType>('default');
    const [rawNodes, setRawNodes] = useState<any[]>([]);
    const [rawEdges, setRawEdges] = useState<any[]>([]);
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [quizTopicStats, setQuizTopicStats] = useState<Record<string, { correct: number; wrong: number }>>({});
    const [hasQuizData, setHasQuizData] = useState(false);

    // Apply layout
    useEffect(() => {
        if (rawNodes.length > 0) {
            const layoutFn = calculateLayouts[layout];
            const layoutedNodes = layoutFn(rawNodes, rawEdges);
            setNodes(layoutedNodes);
            setTimeout(() => fitView({ padding: 0.3 }), 100);
        }
    }, [layout, rawNodes, rawEdges, setNodes, fitView]);

    // Fetch quiz history for this subject and build topic stats
    const fetchQuizStats = useCallback(async () => {
        try {
            const historyRes = await quizAPI.getHistory(subjectId);
            const attempts = historyRes.data || [];
            
            if (attempts.length === 0) return {};

            const topicStats: Record<string, { correct: number; wrong: number }> = {};

            // Fetch detailed results for each attempt to get question-level data
            for (const attempt of attempts.slice(0, 5)) { // Last 5 quizzes
                try {
                    const detailRes = await quizAPI.getAttempt(attempt.id);
                    const questions = detailRes.data.questions || [];
                    
                    for (const q of questions) {
                        const concept = q.source_concept || '';
                        if (!concept) continue;
                        
                        if (!topicStats[concept.toLowerCase()]) {
                            topicStats[concept.toLowerCase()] = { correct: 0, wrong: 0 };
                        }
                        if (q.is_correct) {
                            topicStats[concept.toLowerCase()].correct++;
                        } else {
                            topicStats[concept.toLowerCase()].wrong++;
                        }
                    }
                } catch { /* skip failed attempt fetches */ }
            }

            return topicStats;
        } catch {
            return {};
        }
    }, [subjectId]);

    const fetchMindmap = useCallback(async () => {
        setLoading(true);
        try {
            const [subjectRes, mindmapRes, topicStats] = await Promise.all([
                subjectsAPI.getById(subjectId),
                mindmapAPI.get(subjectId),
                fetchQuizStats(),
            ]);

            setSubject(subjectRes.data);
            setQuizTopicStats(topicStats);
            const hasStats = Object.keys(topicStats).length > 0;
            setHasQuizData(hasStats);

            const flowNodes: Node[] = (mindmapRes.data.nodes || []).map((node: any, i: number) => {
                // Determine quiz status for this node
                let quizStatus: string | null = null;
                if (hasStats) {
                    const label = (node.label || '').toLowerCase();
                    // Check exact match or partial match with quiz topics
                    for (const [topic, stats] of Object.entries(topicStats)) {
                        if (label.includes(topic) || topic.includes(label)) {
                            if (stats.correct > stats.wrong) {
                                quizStatus = 'correct';
                            } else if (stats.wrong > 0) {
                                quizStatus = 'wrong';
                            }
                            break;
                        }
                    }
                }

                return {
                    id: String(node.id),
                    type: 'concept',
                    position: { x: node.x_position ?? i * 200, y: node.y_position ?? i * 100 },
                    data: {
                        label: node.label,
                        description: node.description || null,
                        status: node.status || 'learning',
                        mastery_level: node.mastery_level || 0,
                        quizStatus,
                    },
                };
            });

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
    }, [subjectId, setNodes, setEdges, fetchQuizStats]);

    useEffect(() => { fetchMindmap(); }, [fetchMindmap]);

    const handleNodeClick = useCallback((event: any, node: Node) => {
        setSelectedNode(node.data);
        setSelectedNodeId(node.id);
    }, []);

    // Get quiz stats for the selected node
    const selectedQuizStats = useMemo(() => {
        if (!selectedNode || !hasQuizData) return null;
        const label = (selectedNode.label || '').toLowerCase();
        for (const [topic, stats] of Object.entries(quizTopicStats)) {
            if (label.includes(topic) || topic.includes(label)) {
                return stats;
            }
        }
        return null;
    }, [selectedNode, quizTopicStats, hasQuizData]);

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
                                <p className="text-xs text-slate-400">Knowledge Map {hasQuizData && '• Quiz results applied'}</p>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <StatsBar nodes={nodes} hasQuizData={hasQuizData} />
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
                                nodeColor={n => {
                                    if (n.data?.quizStatus === 'correct') return '#22c55e';
                                    if (n.data?.quizStatus === 'wrong') return '#ef4444';
                                    if (n.data?.status === 'strong') return '#22c55e';
                                    if (n.data?.status === 'weak') return '#ef4444';
                                    return '#8b5cf6';
                                }}
                            />
                        </ReactFlow>

                        <LayoutSwitcher current={layout} onChange={setLayout} />
                        <Legend hasQuizData={hasQuizData} />

                        <AnimatePresence>
                            {selectedNode && (
                                <ConceptPanel
                                    key="concept-panel"
                                    node={selectedNode}
                                    nodeId={selectedNodeId}
                                    onClose={() => { setSelectedNode(null); setSelectedNodeId(null); }}
                                    onStudy={handleStudy}
                                    onQuiz={handleQuiz}
                                    loading={actionLoading}
                                    quizStats={selectedQuizStats}
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
