/**
 * MindMap Page
 */
'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import ReactFlow, {
    Node,
    Edge,
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react';
import { Button, Card, CardContent } from '@/components/ui';
import { mindmapAPI, subjectsAPI } from '@/lib/api';
import { getMasteryColor } from '@/lib/utils';

// Custom Node Component
function ConceptNode({ data }: { data: any }) {
    return (
        <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className={`
        px-4 py-3 rounded-xl border-2 min-w-[120px] text-center cursor-pointer
        transition-all hover:shadow-lg
        ${data.status === 'weak'
                    ? 'border-red-500 bg-red-500/10 hover:shadow-red-500/20'
                    : data.status === 'strong'
                        ? 'border-green-500 bg-green-500/10 hover:shadow-green-500/20'
                        : 'border-violet-500 bg-violet-500/10 hover:shadow-violet-500/20'
                }
      `}
        >
            <p className="text-white font-medium text-sm">{data.label}</p>
            <div className="mt-2 h-1 rounded-full bg-slate-700 overflow-hidden">
                <div
                    className="h-full transition-all"
                    style={{
                        width: `${(data.mastery_level || 0) * 100}%`,
                        backgroundColor: getMasteryColor(data.mastery_level || 0),
                    }}
                />
            </div>
        </motion.div>
    );
}

const nodeTypes = {
    concept: ConceptNode,
};

export default function MindMapPage() {
    const params = useParams();
    const router = useRouter();
    const subjectId = params.subjectId as string;

    const [subject, setSubject] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [selectedNode, setSelectedNode] = useState<any>(null);
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [subjectRes, mindmapRes] = await Promise.all([
                    subjectsAPI.getById(subjectId),
                    mindmapAPI.get(subjectId),
                ]);

                setSubject(subjectRes.data);

                // Convert to ReactFlow format
                const flowNodes: Node[] = mindmapRes.data.nodes.map((node: any) => ({
                    id: node.id,
                    type: 'concept',
                    position: { x: node.x_position, y: node.y_position },
                    data: {
                        label: node.label,
                        description: node.description,
                        mastery_level: node.mastery_level,
                        status: node.status,
                    },
                }));

                const flowEdges: Edge[] = mindmapRes.data.edges.map((edge: any) => ({
                    id: edge.id,
                    source: edge.source_node_id,
                    target: edge.target_node_id,
                    type: 'smoothstep',
                    animated: true,
                    style: { stroke: '#8b5cf6', strokeWidth: 2 },
                    markerEnd: {
                        type: MarkerType.ArrowClosed,
                        color: '#8b5cf6',
                    },
                }));

                setNodes(flowNodes);
                setEdges(flowEdges);
            } catch (error) {
                console.error('Failed to fetch mindmap:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [subjectId, setNodes, setEdges]);

    const onNodeClick = useCallback((event: any, node: Node) => {
        setSelectedNode(node.data);
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 flex flex-col">
            {/* Header */}
            <header className="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 px-4 py-3 z-10">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard')}>
                            <ArrowLeft className="w-4 h-4 mr-2" />
                            Back
                        </Button>
                        <div className="flex items-center gap-2">
                            <span className="text-xl">{subject?.icon || '🧠'}</span>
                            <div>
                                <h1 className="text-white font-medium">{subject?.name} Mind Map</h1>
                                <p className="text-xs text-slate-400">Click nodes to see details</p>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            {/* MindMap */}
            <div className="flex-1 relative">
                {nodes.length > 0 ? (
                    <ReactFlow
                        nodes={nodes}
                        edges={edges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onNodeClick={onNodeClick}
                        nodeTypes={nodeTypes}
                        fitView
                        className="bg-slate-950"
                    >
                        <Background color="#334155" gap={20} />
                        <Controls className="bg-slate-800 border-slate-700 rounded-lg" />
                        <MiniMap
                            nodeColor={(node) => getMasteryColor(node.data?.mastery_level || 0)}
                            className="bg-slate-800 border-slate-700 rounded-lg"
                        />
                    </ReactFlow>
                ) : (
                    <div className="h-full flex items-center justify-center">
                        <div className="text-center">
                            <AlertCircle className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                            <h2 className="text-xl font-semibold text-white mb-2">No Concepts Yet</h2>
                            <p className="text-slate-400 mb-6">
                                Start a learning session to build your mind map
                            </p>
                            <Button onClick={() => router.push('/learn')}>
                                Start Learning
                            </Button>
                        </div>
                    </div>
                )}

                {/* Node Details Panel */}
                {selectedNode && (
                    <motion.div
                        initial={{ x: 300, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        className="absolute top-4 right-4 w-80"
                    >
                        <Card>
                            <CardContent>
                                <div className="flex items-start justify-between mb-4">
                                    <div>
                                        <h3 className="text-lg font-semibold text-white">{selectedNode.label}</h3>
                                        <span className={`text-xs px-2 py-0.5 rounded-full ${selectedNode.status === 'weak'
                                                ? 'bg-red-500/20 text-red-400'
                                                : selectedNode.status === 'strong'
                                                    ? 'bg-green-500/20 text-green-400'
                                                    : 'bg-violet-500/20 text-violet-400'
                                            }`}>
                                            {selectedNode.status}
                                        </span>
                                    </div>
                                    <button
                                        onClick={() => setSelectedNode(null)}
                                        className="text-slate-400 hover:text-white"
                                    >
                                        ×
                                    </button>
                                </div>

                                <div className="mb-4">
                                    <p className="text-sm text-slate-400 mb-2">Mastery Level</p>
                                    <div className="h-2 rounded-full bg-slate-700">
                                        <div
                                            className="h-full rounded-full transition-all"
                                            style={{
                                                width: `${(selectedNode.mastery_level || 0) * 100}%`,
                                                backgroundColor: getMasteryColor(selectedNode.mastery_level || 0),
                                            }}
                                        />
                                    </div>
                                    <p className="text-xs text-slate-500 mt-1">
                                        {Math.round((selectedNode.mastery_level || 0) * 100)}%
                                    </p>
                                </div>

                                {selectedNode.description && (
                                    <p className="text-sm text-slate-400">{selectedNode.description}</p>
                                )}
                            </CardContent>
                        </Card>
                    </motion.div>
                )}
            </div>
        </div>
    );
}
