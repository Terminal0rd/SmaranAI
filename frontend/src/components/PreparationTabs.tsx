/**
 * Preparation Tabs Component
 * Displays 9-tab interface for semester preparation results
 */
'use client';

import { useState } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui';
import ReactMarkdown from 'react-markdown';
import {
    BookOpen,
    FileText,
    HelpCircle,
    FileQuestion,
    Target,
    ClipboardCheck,
    Mic,
    Presentation,
    Calendar,
    Loader2
} from 'lucide-react';
import { preparationAPI } from '@/lib/api';

interface PreparationTabsProps {
    data: any;
}

export function PreparationTabs({ data }: PreparationTabsProps) {
    const [activeTab, setActiveTab] = useState('syllabus');

    // Detect which sections already have content (from history load)
    const getInitialLoadedSections = (): Set<string> => {
        const sections = new Set(['syllabus']);
        if (data.notes && Array.isArray(data.notes) && data.notes.length > 0) {
            sections.add('notes');
        }
        if ((data.five_mark_questions?.length > 0) || (data.ten_mark_questions?.length > 0) || (data.predicted_questions?.length > 0)) {
            sections.add('questions');
            sections.add('5m');
            sections.add('10m');
            sections.add('predicted');
        }
        if (data.mock_test && typeof data.mock_test === 'object' && Object.keys(data.mock_test).length > 0) {
            sections.add('mock_viva');
            sections.add('mock');
            sections.add('viva');
        }
        if (data.viva_questions && Array.isArray(data.viva_questions) && data.viva_questions.length > 0) {
            sections.add('mock_viva');
            sections.add('mock');
            sections.add('viva');
        }
        if (data.ppt_content && Array.isArray(data.ppt_content) && data.ppt_content.length > 0) {
            sections.add('ppt_plan');
            sections.add('ppt');
            sections.add('plan');
        }
        if (data.study_plan && Array.isArray(data.study_plan) && data.study_plan.length > 0) {
            sections.add('ppt_plan');
            sections.add('ppt');
            sections.add('plan');
        }
        return sections;
    };

    // Track loaded sections - pre-populated from existing data
    const [loadedSections, setLoadedSections] = useState<Set<string>>(getInitialLoadedSections);
    const [loadingSection, setLoadingSection] = useState<string | null>(null);

    // Store section data - initialized from existing data (history or fresh)
    const [sectionData, setSectionData] = useState<any>({
        notes: data.notes || [],
        five_mark_questions: data.five_mark_questions || [],
        ten_mark_questions: data.ten_mark_questions || [],
        predicted_questions: data.predicted_questions || [],
        mock_test: data.mock_test || {},
        viva_questions: data.viva_questions || [],
        ppt_content: data.ppt_content || [],
        study_plan: data.study_plan || []
    });

    // Map tab values to section names
    const tabToSection: Record<string, string> = {
        'notes': 'notes',
        '5m': 'questions',
        '10m': 'questions',
        'predicted': 'questions',
        'mock': 'mock_viva',
        'viva': 'mock_viva',
        'ppt': 'ppt_plan',
        'plan': 'ppt_plan'
    };

    // Handle tab change with on-demand loading
    const handleTabChange = async (tabValue: string) => {
        setActiveTab(tabValue);

        // Skip if syllabus (always loaded)
        if (tabValue === 'syllabus') {
            return;
        }

        const sectionName = tabToSection[tabValue];
        if (!sectionName) {
            return;
        }

        // Check if this section already has content in the data
        const sectionHasContent = () => {
            switch (sectionName) {
                case 'notes':
                    return sectionData.notes && sectionData.notes.length > 0;
                case 'questions':
                    return sectionData.five_mark_questions && sectionData.five_mark_questions.length > 0;
                case 'mock_viva':
                    return sectionData.mock_test && Object.keys(sectionData.mock_test).length > 0;
                case 'ppt_plan':
                    return sectionData.ppt_content && sectionData.ppt_content.length > 0;
                default:
                    return false;
            }
        };

        // Skip if already loaded or already has content
        if (loadedSections.has(tabValue) || sectionHasContent()) {
            // Mark as loaded if it has content but wasn't marked yet
            if (sectionHasContent() && !loadedSections.has(tabValue)) {
                setLoadedSections(prev => new Set([...prev, sectionName, tabValue]));
            }
            return;
        }

        // Load section on-demand (only if truly missing)
        setLoadingSection(tabValue);
        try {
            console.log('DEBUG: Calling generateSection with prep_id:', data.id, 'section:', sectionName);
            const result = await preparationAPI.generateSection({
                prep_id: data.id,
                section: sectionName,
                subject: data.subject,
                university: data.university,
                exam_type: data.exam_type || 'Regular',
                exam_date: data.exam_date
            });

            // Update section data based on what was generated
            setSectionData((prev: any) => ({
                ...prev,
                ...result
            }));

            // Mark section as loaded
            setLoadedSections(prev => new Set([...prev, sectionName, tabValue]));
        } catch (error) {
            console.error(`Failed to load ${sectionName}:`, error);
        } finally {
            setLoadingSection(null);
        }
    };

    // Loading component
    const LoadingState = ({ section }: { section: string }) => (
        <div className="flex flex-col items-center justify-center py-12 space-y-4">
            <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
            <p className="text-slate-400">Generating {section}...</p>
            <p className="text-xs text-slate-500">This may take 15-30 seconds</p>
        </div>
    );


    return (
        <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
            <TabsList className="grid grid-cols-9 w-full mb-6 bg-slate-900/50 p-1 gap-1">
                <TabsTrigger value="syllabus" className="text-xs flex items-center gap-1">
                    <BookOpen className="w-3 h-3" />
                    <span className="hidden sm:inline">Syllabus</span>
                </TabsTrigger>
                <TabsTrigger value="notes" className="text-xs flex items-center gap-1">
                    <FileText className="w-3 h-3" />
                    <span className="hidden sm:inline">Notes</span>
                </TabsTrigger>
                <TabsTrigger value="5m" className="text-xs">5M</TabsTrigger>
                <TabsTrigger value="10m" className="text-xs">10M</TabsTrigger>
                <TabsTrigger value="predicted" className="text-xs flex items-center gap-1">
                    <Target className="w-3 h-3" />
                    <span className="hidden sm:inline">Predicted</span>
                </TabsTrigger>
                <TabsTrigger value="mock" className="text-xs flex items-center gap-1">
                    <ClipboardCheck className="w-3 h-3" />
                    <span className="hidden sm:inline">Mock</span>
                </TabsTrigger>
                <TabsTrigger value="viva" className="text-xs flex items-center gap-1">
                    <Mic className="w-3 h-3" />
                    <span className="hidden sm:inline">Viva</span>
                </TabsTrigger>
                <TabsTrigger value="ppt" className="text-xs flex items-center gap-1">
                    <Presentation className="w-3 h-3" />
                    <span className="hidden sm:inline">PPT</span>
                </TabsTrigger>
                <TabsTrigger value="plan" className="text-xs flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    <span className="hidden sm:inline">Plan</span>
                </TabsTrigger>
            </TabsList>

            {/* 1. Syllabus */}
            <TabsContent value="syllabus">
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <BookOpen className="w-5 h-5 text-violet-400" />
                            Syllabus Breakdown
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {data.syllabus?.map((unit: any, idx: number) => (
                            <div key={idx} className="p-4 bg-slate-800/50 rounded-lg">
                                <h3 className="text-lg font-semibold text-white mb-2">
                                    Unit {unit.unit_number}: {unit.unit_title}
                                </h3>
                                <div className="flex flex-wrap gap-2 mb-2">
                                    {unit.topics?.map((topic: string, i: number) => (
                                        <span key={i} className="px-2 py-1 bg-violet-500/20 text-violet-300 text-sm rounded">
                                            {topic}
                                        </span>
                                    ))}
                                </div>
                                <p className="text-xs text-slate-400">
                                    Estimated Study Time: {unit.estimated_hours} hours
                                </p>
                            </div>
                        ))}
                    </CardContent>
                </Card>
            </TabsContent>

            {/* 2. Smart Notes */}
            <TabsContent value="notes">
                {loadingSection === 'notes' ? (
                    <LoadingState section="notes" />
                ) : (
                    <div className="space-y-4">
                        {sectionData.notes?.map((note: any, idx: number) => (
                            <Card key={idx}>
                                <CardHeader>
                                    <CardTitle className="text-lg">{note.topic}</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-3">
                                    <div className="prose prose-invert max-w-none">
                                        <ReactMarkdown>{note.explanation}</ReactMarkdown>
                                    </div>

                                    {note.key_definitions?.length > 0 && (
                                        <div>
                                            <h4 className="font-semibold text-white mb-2">Key Definitions:</h4>
                                            <ul className="list-disc list-inside space-y-1 text-slate-300">
                                                {note.key_definitions.map((def: string, i: number) => (
                                                    <li key={i}>{def}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}

                                    {note.formulas?.length > 0 && (
                                        <div>
                                            <h4 className="font-semibold text-white mb-2">Formulas:</h4>
                                            <div className="space-y-1">
                                                {note.formulas.map((formula: string, i: number) => (
                                                    <code key={i} className="block p-2 bg-slate-800 rounded text-green-300">
                                                        {formula}
                                                    </code>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {note.important_points?.length > 0 && (
                                        <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded">
                                            <h4 className="font-semibold text-amber-400 mb-2">Important Points:</h4>
                                            <ul className="list-disc list-inside space-y-1 text-slate-300">
                                                {note.important_points.map((point: string, i: number) => (
                                                    <li key={i}>{point}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}
            </TabsContent>

            {/* 3. 5-Mark Questions */}
            <TabsContent value="5m">
                {loadingSection === '5m' ? (
                    <LoadingState section="5-mark questions" />
                ) : (
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <FileQuestion className="w-5 h-5 text-blue-400" />
                                5-Mark Questions
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                            {sectionData.five_mark_questions?.map((q: any, idx: number) => (
                                <div key={idx} className="p-4 bg-slate-800/50 rounded-lg">
                                    <div className="flex justify-between items-start mb-1">
                                        <span className="text-sm text-slate-400">Q{idx + 1}. {q.unit}</span>
                                        <span className={`text-xs px-2 py-1 rounded ${q.difficulty === 'Easy' ? 'bg-green-500/20 text-green-400' :
                                            q.difficulty === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                                                'bg-red-500/20 text-red-400'
                                            }`}>{q.difficulty}</span>
                                    </div>
                                    <p className="text-white mb-2">{q.question}</p>
                                    {q.hint && (
                                        <p className="text-sm text-violet-400 italic">Hint: {q.hint}</p>
                                    )}
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                )}
            </TabsContent>

            {/* 4. 10-Mark Questions */}
            <TabsContent value="10m">
                {loadingSection === '10m' ? (
                    <LoadingState section="10-mark questions" />
                ) : (
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <FileQuestion className="w-5 h-5 text-indigo-400" />
                                10-Mark Questions
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                            {sectionData.ten_mark_questions?.map((q: any, idx: number) => (
                                <div key={idx} className="p-4 bg-slate-800/50 rounded-lg">
                                    <div className="flex justify-between items-start mb-1">
                                        <span className="text-sm text-slate-400">Q{idx + 1}. {q.unit}</span>
                                        <span className={`text-xs px-2 py-1 rounded ${q.difficulty === 'Easy' ? 'bg-green-500/20 text-green-400' :
                                            q.difficulty === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                                                'bg-red-500/20 text-red-400'
                                            }`}>{q.difficulty}</span>
                                    </div>
                                    <p className="text-white mb-2">{q.question}</p>
                                    {q.hint && (
                                        <p className="text-sm text-violet-400 italic">Hint: {q.hint}</p>
                                    )}
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                )}
            </TabsContent>

            {/* 5. Predicted Questions */}
            <TabsContent value="predicted">
                {loadingSection === 'predicted' ? (
                    <LoadingState section="predicted questions" />
                ) : (
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Target className="w-5 h-5 text-amber-400" />
                                Predicted Important Questions
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                            {sectionData.predicted_questions?.map((q: any, idx: number) => (
                                <div key={idx} className="p-4 bg-slate-800/50 rounded-lg border-l-4 border-amber-500">
                                    <div className="flex justify-between items-start mb-2">
                                        <span className={`text-xs px-2 py-1 rounded ${q.probability === 'High' ? 'bg-red-500/20 text-red-400' :
                                            q.probability === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                                                'bg-green-500/20 text-green-400'
                                            }`}>{q.probability} Probability</span>
                                        <span className="text-sm text-slate-400">{q.unit} • {q.marks}M</span>
                                    </div>
                                    <p className="text-white mb-2">{q.question}</p>
                                    <p className="text-sm text-slate-400 italic">Why: {q.reason}</p>
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                )}
            </TabsContent>

            {/* 6. Mock Test */}
            <TabsContent value="mock">
                {loadingSection === 'mock' ? (
                    <LoadingState section="mock test" />
                ) : (
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <ClipboardCheck className="w-5 h-5 text-green-400" />
                                Mock Test
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            {Object.entries(sectionData.mock_test || {}).map(([key, section]: [string, any]) => (
                                <div key={key} className="border border-slate-700 rounded-lg p-4">
                                    <div className="flex justify-between items-center mb-3">
                                        <h3 className="text-lg font-semibold text-white">{section.section_name}</h3>
                                        <span className="text-sm text-violet-400">{section.total_marks} marks</span>
                                    </div>
                                    <p className="text-sm text-slate-400 mb-4 italic">{section.instructions}</p>
                                    <div className="space-y-3">
                                        {section.questions?.map((q: any, idx: number) => (
                                            <div key={idx} className="p-3 bg-slate-900/50 rounded">
                                                <p className="text-white">Q{idx + 1}. {q.question} ({q.marks}M)</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                )}
            </TabsContent>

            {/* 7. Viva Questions */}
            <TabsContent value="viva">
                {loadingSection === 'viva' ? (
                    <LoadingState section="viva questions" />
                ) : (
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Mic className="w-5 h-5 text-pink-400" />
                                Viva/Oral Questions
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                            {sectionData.viva_questions?.map((q: any, idx: number) => (
                                <div key={idx} className="p-4 bg-slate-800/50 rounded-lg">
                                    <div className="flex justify-between items-start mb-2">
                                        <span className="text-sm text-slate-400">{q.unit}</span>
                                    </div>
                                    <p className="text-white font-medium mb-2">Q: {q.question}</p>
                                    <div className="p-3 bg-slate-900/50 rounded">
                                        <span className="text-xs text-green-400 font-semibold">Expected Answer:</span>
                                        <p className="text-slate-300 text-sm mt-1">{q.expected_answer}</p>
                                    </div>
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                )}
            </TabsContent>

            {/* 8. PPT Content */}
            <TabsContent value="ppt">
                {loadingSection === 'ppt' ? (
                    <LoadingState section="PPT content" />
                ) : (
                    <div className="grid gap-4">
                        {sectionData.ppt_content?.map((slide: any) => (
                            <Card key={slide.slide_number}>
                                <CardHeader>
                                    <CardTitle className="text-base flex items-center gap-2">
                                        <span className="text-violet-400">Slide {slide.slide_number}</span>
                                        <span>•</span>
                                        <span>{slide.title}</span>
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <ul className="list-disc list-inside space-y-1 text-slate-300 mb-3">
                                        {slide.bullet_points?.map((point: string, i: number) => (
                                            <li key={i}>{point}</li>
                                        ))}
                                    </ul>
                                    {slide.diagram_suggestion && (
                                        <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded">
                                            <span className="text-xs text-blue-400">📊 Diagram: </span>
                                            <span className="text-sm text-slate-300">{slide.diagram_suggestion}</span>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}
            </TabsContent>

            {/* 9. Study Plan */}
            <TabsContent value="plan">
                {loadingSection === 'plan' ? (
                    <LoadingState section="study plan" />
                ) : (
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Calendar className="w-5 h-5 text-cyan-400" />
                                Study Planner
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2">
                                {sectionData.study_plan?.map((day: any) => (
                                    <div key={day.day_number} className={`p-4 rounded-lg ${day.mock_test ? 'bg-red-500/10 border border-red-500/20' :
                                        day.revision ? 'bg-green-500/10 border border-green-500/20' :
                                            'bg-slate-800/50'
                                        }`}>
                                        <div className="flex justify-between items-center mb-2">
                                            <span className="font-semibold text-white">
                                                Day {day.day_number}
                                                {day.date && <span className="text-slate-400 ml-2 text-sm">({day.date})</span>}
                                            </span>
                                            {day.mock_test && <span className="text-xs px-2 py-1 bg-red-500/20 text-red-400 rounded">Mock Test</span>}
                                            {day.revision && <span className="text-xs px-2 py-1 bg-green-500/20 text-green-400 rounded">Revision</span>}
                                        </div>
                                        <ul className="list-disc list-inside space-y-1 text-slate-300 text-sm">
                                            {day.tasks?.map((task: string, i: number) => (
                                                <li key={i}>{task}</li>
                                            ))}
                                        </ul>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                )}
            </TabsContent>
        </Tabs>
    );
}
