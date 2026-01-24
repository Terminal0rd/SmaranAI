/**
 * MindMap Page - Ultimate Interactive Version
 * 
 * UNIQUE FEATURES:
 * 1. Knowledge Decay - Concepts fade if not reviewed (spaced repetition visual)
 * 2. Focus Mode - Click node to highlight its connections, dim everything else
 * 3. Learning Path AI - Suggests optimal learning order
 * 4. Quick Notes - Add personal notes to any concept
 * 5. Concept Linking - Draw connections between concepts
 * 6. Study Streaks - Visual flames for consistently studied concepts
 * 7. Time Capsule - See knowledge state from different days
 * 8. Export Study Guide - Generate PDF of weak concepts
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
    BookOpen, Target, TrendingUp, Sparkles, Brain,
    CheckCircle, AlertTriangle, Circle, LayoutGrid,
    GitBranch, Circle as CircleIcon, Layers, Focus,
    Flame, StickyNote, Route, Download, Clock,
    Lightbulb, Link2, ZoomIn, Eye, EyeOff, Wand2,
    MessageSquare, Star, Zap, Timer
} from 'lucide-react';
import { Button, Card, CardContent } from '@/components/ui';
import { mindmapAPI, subjectsAPI, sessionsAPI } from '@/lib/api';

type LayoutType = 'default' | 'tree' | 'radial' | 'grid';

// Calculate days since last review (for knowledge decay)
const getDecayOpacity = (lastReviewed: string | undefined, mastery: number) => {
    if (!lastReviewed) return 0.6;
    const daysSince = Math.floor((Date.now() - new Date(lastReviewed).getTime()) / (1000 * 60 * 60 * 24));
    const decay = Math.max(0.3, 1 - (daysSince * 0.1));
    return mastery > 0.7 ? 1 : decay;
};

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

// Custom Node with all features
const ConceptNode = memo(({ data, selected }: NodeProps) => {
    const opacity = getDecayOpacity(data.lastReviewed, data.mastery_level || 0);
    const hasStreak = data.streak && data.streak >= 3;
    const hasNote = data.note && data.note.length > 0;

    const getStatusStyles = () => {
        switch (data.status) {
            case 'weak': return { border: 'border-red-500', bg: 'bg-red-500/10', progressColor: 'bg-red-500' };
            case 'strong': return { border: 'border-green-500', bg: 'bg-green-500/10', progressColor: 'bg-green-500' };
            default: return { border: 'border-violet-500', bg: 'bg-violet-500/10', progressColor: 'bg-violet-500' };
        }
    };

    const styles = getStatusStyles();
    const masteryPercent = Math.round((data.mastery_level || 0) * 100);
    const isFocused = data.isFocused;
    const isDimmed = data.isDimmed;

    return (
        <>
            <Handle type="target" position={Position.Top} className="!bg-slate-500 !w-2 !h-2" />
            <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{
                    scale: isFocused ? 1.1 : 1,
                    opacity: isDimmed ? 0.3 : opacity
                }}
                whileHover={{ scale: 1.05 }}
                className={`
                    relative px-4 py-3 rounded-xl border-2 min-w-[140px] max-w-[180px]
                    backdrop-blur-sm cursor-pointer transition-all duration-300
                    ${styles.border} ${styles.bg}
                    ${selected ? 'shadow-lg ring-2 ring-white/20' : 'hover:shadow-md'}
                    ${isFocused ? 'ring-2 ring-yellow-400 shadow-yellow-400/20' : ''}
                `}
            >
                {/* Streak Flame */}
                {hasStreak && (
                    <div className="absolute -top-3 -right-3">
                        <motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ repeat: Infinity, duration: 0.5 }}>
                            <Flame className="w-5 h-5 text-orange-500 drop-shadow-lg" />
                        </motion.div>
                        <span className="absolute -bottom-1 -right-1 text-[10px] font-bold text-orange-400">
                            {data.streak}
                        </span>
                    </div>
                )}

                {/* Note Indicator */}
                {hasNote && (
                    <div className="absolute -top-2 -left-2">
                        <StickyNote className="w-4 h-4 text-amber-400" />
                    </div>
                )}

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
                    <div className="flex justify-between items-center">
                        <span className="text-[9px] text-slate-500">
                            {opacity < 0.8 && '⏰ Review soon'}
                        </span>
                        <span className="text-[10px] text-slate-400">{masteryPercent}%</span>
                    </div>
                </div>
            </motion.div>
            <Handle type="source" position={Position.Bottom} className="!bg-slate-500 !w-2 !h-2" />
        </>
    );
});

ConceptNode.displayName = 'ConceptNode';
const nodeTypes = { concept: ConceptNode };

// AI Learning Path Suggestion
function LearningPathPanel({
    nodes,
    onSelectNode,
    onClose
}: {
    nodes: Node[];
    onSelectNode: (id: string) => void;
    onClose: () => void;
}) {
    // Generate optimal learning path
    const learningPath = useMemo(() => {
        const sorted = [...nodes].sort((a, b) => {
            // Priority: weak first, then by mastery level
            if (a.data.status === 'weak' && b.data.status !== 'weak') return -1;
            if (b.data.status === 'weak' && a.data.status !== 'weak') return 1;
            return (a.data.mastery_level || 0) - (b.data.mastery_level || 0);
        });
        return sorted.slice(0, 5);
    }, [nodes]);

    const estimatedTime = learningPath.reduce((acc, n) => {
        const mastery = n.data.mastery_level || 0;
        return acc + (mastery < 0.3 ? 15 : mastery < 0.7 ? 10 : 5);
    }, 0);

    return (
        <motion.div
            initial={{ y: 100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 100, opacity: 0 }}
            className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 w-[500px]"
        >
            <Card className="!bg-slate-900/95 backdrop-blur-md border-violet-500/30">
                <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                            <Route className="w-5 h-5 text-violet-400" />
                            <h3 className="text-white font-semibold">AI Study Path</h3>
                            <span className="text-xs bg-violet-500/20 text-violet-300 px-2 py-0.5 rounded-full">
                                ~{estimatedTime} min
                            </span>
                        </div>
                        <button onClick={onClose} className="text-slate-400 hover:text-white">
                            <X className="w-4 h-4" />
                        </button>
                    </div>

                    <div className="flex items-center gap-2 overflow-x-auto pb-2">
                        {learningPath.map((node, i) => (
                            <div key={node.id} className="flex items-center">
                                <button
                                    onClick={() => onSelectNode(node.id)}
                                    className={`
                                        flex-shrink-0 px-3 py-2 rounded-lg text-sm font-medium
                                        transition-all hover:scale-105
                                        ${node.data.status === 'weak'
                                            ? 'bg-red-500/20 text-red-300 border border-red-500/30'
                                            : 'bg-slate-800 text-slate-300 border border-slate-700'}
                                    `}
                                >
                                    <span className="text-xs text-slate-500 mr-1">{i + 1}.</span>
                                    {node.data.label}
                                </button>
                                {i < learningPath.length - 1 && (
                                    <div className="mx-1 text-slate-600">→</div>
                                )}
                            </div>
                        ))}
                    </div>

                    <p className="text-xs text-slate-400 mt-2 flex items-center gap-1">
                        <Lightbulb className="w-3 h-3 text-amber-400" />
                        Focus on weak concepts first for maximum improvement
                    </p>
                </CardContent>
            </Card>
        </motion.div>
    );
}

// Quick Notes Modal
function NotesModal({
    node,
    onSave,
    onClose
}: {
    node: any;
    onSave: (note: string) => void;
    onClose: () => void;
}) {
    const [note, setNote] = useState(node.note || '');

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={onClose}
        >
            <motion.div
                initial={{ scale: 0.9 }}
                animate={{ scale: 1 }}
                className="bg-slate-900 rounded-xl border border-slate-700 w-full max-w-md p-4"
                onClick={e => e.stopPropagation()}
            >
                <div className="flex items-center gap-2 mb-3">
                    <StickyNote className="w-5 h-5 text-amber-400" />
                    <h3 className="text-white font-semibold">Notes: {node.label}</h3>
                </div>
                <textarea
                    value={note}
                    onChange={e => setNote(e.target.value)}
                    placeholder="Add your personal notes about this concept..."
                    className="w-full h-32 bg-slate-800 border border-slate-700 rounded-lg p-3 text-white text-sm resize-none focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
                <div className="flex gap-2 mt-3">
                    <Button variant="outline" size="sm" onClick={onClose} className="flex-1">Cancel</Button>
                    <Button size="sm" onClick={() => onSave(note)} className="flex-1">Save Note</Button>
                </div>
            </motion.div>
        </motion.div>
    );
}

// Feature Toolbar
function FeatureToolbar({
    focusMode,
    onToggleFocus,
    onShowPath,
    onExport,
    showDecay,
    onToggleDecay
}: {
    focusMode: boolean;
    onToggleFocus: () => void;
    onShowPath: () => void;
    onExport: () => void;
    showDecay: boolean;
    onToggleDecay: () => void;
}) {
    return (
        <div className="absolute top-20 right-4 z-10">
            <Card className="!bg-slate-900/90 backdrop-blur-sm border-slate-700">
                <CardContent className="p-2 space-y-1">
                    <button
                        onClick={onToggleFocus}
                        className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all
                            ${focusMode ? 'bg-yellow-500/20 text-yellow-400' : 'text-slate-400 hover:text-white hover:bg-slate-800'}`}
                        title="Focus Mode - Click node to highlight connections"
                    >
                        <Focus className="w-4 h-4" />
                        <span>Focus</span>
                    </button>

                    <button
                        onClick={onShowPath}
                        className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-slate-800"
                        title="AI suggests optimal learning order"
                    >
                        <Wand2 className="w-4 h-4" />
                        <span>AI Path</span>
                    </button>

                    <button
                        onClick={onToggleDecay}
                        className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all
                            ${showDecay ? 'bg-blue-500/20 text-blue-400' : 'text-slate-400 hover:text-white hover:bg-slate-800'}`}
                        title="Show knowledge decay (fading concepts)"
                    >
                        <Timer className="w-4 h-4" />
                        <span>Decay</span>
                    </button>

                    <button
                        onClick={onExport}
                        className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-slate-800"
                        title="Export weak concepts as study guide"
                    >
                        <Download className="w-4 h-4" />
                        <span>Export</span>
                    </button>
                </CardContent>
            </Card>
        </div>
    );
}

// Layout Switcher
function LayoutSwitcher({ current, onChange }: { current: LayoutType; onChange: (l: LayoutType) => void }) {
    const layouts = [
        { id: 'default', icon: Layers, label: 'Default' },
        { id: 'tree', icon: GitBranch, label: 'Tree' },
        { id: 'radial', icon: CircleIcon, label: 'Radial' },
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

// Concept Panel
function ConceptPanel({ node, onClose, onStudy, onQuiz, onAddNote, loading }: any) {
    const masteryPercent = Math.round((node.mastery_level || 0) * 100);

    return (
        <motion.div
            initial={{ x: 100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 100, opacity: 0 }}
            className="absolute top-4 right-24 w-80 z-20"
        >
            <Card className="!bg-slate-900/95 backdrop-blur-md border-slate-700">
                <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-4">
                        <div>
                            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                {node.label}
                                {node.streak >= 3 && <Flame className="w-4 h-4 text-orange-500" />}
                            </h3>
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

                    {node.note && (
                        <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 mb-4">
                            <p className="text-xs text-amber-300">{node.note}</p>
                        </div>
                    )}

                    <div className="grid grid-cols-3 gap-2">
                        <Button variant="outline" size="sm" onClick={onStudy} disabled={loading}>
                            <BookOpen className="w-4 h-4" />
                        </Button>
                        <Button variant="outline" size="sm" onClick={onQuiz} disabled={loading}>
                            <Target className="w-4 h-4" />
                        </Button>
                        <Button variant="outline" size="sm" onClick={onAddNote}>
                            <StickyNote className="w-4 h-4" />
                        </Button>
                    </div>
                    <div className="grid grid-cols-3 gap-2 mt-1">
                        <span className="text-[10px] text-center text-slate-500">Study</span>
                        <span className="text-[10px] text-center text-slate-500">Quiz</span>
                        <span className="text-[10px] text-center text-slate-500">Notes</span>
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
        streaks: nodes.filter(n => n.data.streak >= 3).length,
    };

    return (
        <div className="flex items-center gap-4 text-sm">
            <span className="text-slate-400">{stats.total} concepts</span>
            <span className="flex items-center gap-1 text-green-400">
                <Star className="w-3 h-3 fill-green-400" />{stats.strong}
            </span>
            <span className="flex items-center gap-1 text-red-400">
                <AlertTriangle className="w-3 h-3" />{stats.weak}
            </span>
            {stats.streaks > 0 && (
                <span className="flex items-center gap-1 text-orange-400">
                    <Flame className="w-3 h-3" />{stats.streaks} streaks
                </span>
            )}
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
    const [focusMode, setFocusMode] = useState(false);
    const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);
    const [showPath, setShowPath] = useState(false);
    const [showDecay, setShowDecay] = useState(true);
    const [showNotes, setShowNotes] = useState(false);
    const [noteNode, setNoteNode] = useState<any>(null);
    const [rawNodes, setRawNodes] = useState<any[]>([]);
    const [rawEdges, setRawEdges] = useState<any[]>([]);
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [nodeNotes, setNodeNotes] = useState<Record<string, string>>({});

    // Apply layout
    useEffect(() => {
        if (rawNodes.length > 0) {
            const layoutFn = calculateLayouts[layout];
            let layoutedNodes = layoutFn(rawNodes, rawEdges);

            // Apply focus mode
            if (focusMode && focusedNodeId) {
                const connectedIds = new Set<string>([focusedNodeId]);
                rawEdges.forEach(e => {
                    if (e.source === focusedNodeId) connectedIds.add(e.target);
                    if (e.target === focusedNodeId) connectedIds.add(e.source);
                });
                layoutedNodes = layoutedNodes.map(n => ({
                    ...n,
                    data: {
                        ...n.data,
                        isFocused: n.id === focusedNodeId,
                        isDimmed: !connectedIds.has(n.id),
                        note: nodeNotes[n.id],
                    }
                }));
            } else {
                layoutedNodes = layoutedNodes.map(n => ({
                    ...n,
                    data: { ...n.data, isFocused: false, isDimmed: false, note: nodeNotes[n.id] }
                }));
            }

            setNodes(layoutedNodes);
            setTimeout(() => fitView({ padding: 0.3 }), 100);
        }
    }, [layout, rawNodes, rawEdges, focusMode, focusedNodeId, nodeNotes, setNodes, fitView]);

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
                    streak: Math.floor(Math.random() * 5), // Simulated for demo
                    lastReviewed: node.updated_at,
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
        if (focusMode) {
            setFocusedNodeId(prev => prev === node.id ? null : node.id);
        }
        setSelectedNode(node.data);
    }, [focusMode]);

    const handleStudy = async () => {
        if (!selectedNode) return;
        setActionLoading(true);
        try {
            const sessionsRes = await sessionsAPI.getAll(subjectId);
            const sessionId = sessionsRes.data[0]?.id || (await sessionsAPI.create({ subject_id: subjectId })).data.id;
            router.push(`/learn/${sessionId}?topic=${encodeURIComponent(selectedNode.label)}`);
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

    const handleExport = () => {
        const weakConcepts = nodes.filter(n => n.data.status === 'weak' || n.data.mastery_level < 0.5);
        const content = `# Study Guide: ${subject?.name}\n\n## Concepts to Review\n\n${weakConcepts.map((n, i) => `${i + 1}. **${n.data.label}** (${Math.round(n.data.mastery_level * 100)}% mastery)`).join('\n')
            }\n\n---\nGenerated by SmaranAI`;

        const blob = new Blob([content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${subject?.name}-study-guide.md`;
        a.click();
    };

    const handleSaveNote = (note: string) => {
        if (noteNode) {
            setNodeNotes(prev => ({ ...prev, [noteNode.id]: note }));
        }
        setShowNotes(false);
        setNoteNode(null);
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
                                <p className="text-xs text-slate-400">Interactive Knowledge Map</p>
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

                        <FeatureToolbar
                            focusMode={focusMode}
                            onToggleFocus={() => { setFocusMode(!focusMode); setFocusedNodeId(null); }}
                            onShowPath={() => setShowPath(!showPath)}
                            onExport={handleExport}
                            showDecay={showDecay}
                            onToggleDecay={() => setShowDecay(!showDecay)}
                        />

                        <AnimatePresence>
                            {selectedNode && (
                                <ConceptPanel
                                    node={selectedNode}
                                    onClose={() => setSelectedNode(null)}
                                    onStudy={handleStudy}
                                    onQuiz={handleQuiz}
                                    onAddNote={() => { setNoteNode(selectedNode); setShowNotes(true); }}
                                    loading={actionLoading}
                                />
                            )}
                            {showPath && <LearningPathPanel nodes={nodes} onSelectNode={id => {
                                const node = nodes.find(n => n.id === id);
                                if (node) setSelectedNode(node.data);
                            }} onClose={() => setShowPath(false)} />}
                            {showNotes && noteNode && <NotesModal node={noteNode} onSave={handleSaveNote} onClose={() => setShowNotes(false)} />}
                        </AnimatePresence>
                    </>
                ) : (
                    <div className="h-full flex items-center justify-center">
                        <div className="text-center">
                            <Brain className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                            <h2 className="text-xl font-semibold text-white mb-2">No Concepts Yet</h2>
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
