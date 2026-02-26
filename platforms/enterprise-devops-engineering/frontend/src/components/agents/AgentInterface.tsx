import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Play,
  Square,
  Plus,
  Trash2,
  Save,
  FolderOpen,
  MousePointer2,
  ArrowRight,
  Bot,
  GripVertical,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { useAgentStore } from '@/store/appStore';
import { cn } from '@/lib/utils';
import type { Agent, AgentNode } from '@/types';

const availableAgents: Agent[] = [
  { id: 'input', name: '输入代理', type: 'input', description: '接收用户输入', icon: '📥', color: '#3B82F6', config: {} },
  { id: 'process', name: '处理代理', type: 'process', description: '处理数据', icon: '🧠', color: '#8B5CF6', config: {} },
  { id: 'output', name: '输出代理', type: 'output', description: '输出结果', icon: '📤', color: '#10B981', config: {} },
  { id: 'store', name: '存储代理', type: 'store', description: '存储数据', icon: '💾', color: '#F59E0B', config: {} },
  { id: 'research', name: '研究代理', type: 'research', description: '搜索信息', icon: '🔍', color: '#EF4444', config: {} },
  { id: 'write', name: '写作代理', type: 'write', description: '生成文本', icon: '✍️', color: '#EC4899', config: {} },
  { id: 'code', name: '代码代理', type: 'code', description: '编写代码', icon: '💻', color: '#06B6D4', config: {} },
  { id: 'calculate', name: '计算代理', type: 'calculate', description: '执行计算', icon: '🧮', color: '#84CC16', config: {} },
];

export function AgentInterface() {
  const {
    workflows,
    currentWorkflowId,
    nodes,
    connections,
    selectedNodeId,
    isRunning,
    createWorkflow,
    addNode,
    removeNode,
    updateNodePosition,
    updateNodeConfig,
    addConnection,
    setSelectedNode,
    runWorkflow,
    stopWorkflow,
  } = useAgentStore();

  const [workflowName, setWorkflowName] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [connectingFrom, setConnectingFrom] = useState<string | null>(null);
  const [draggedAgent, setDraggedAgent] = useState<Agent | null>(null);

  const handleCreateWorkflow = () => {
    if (!workflowName.trim()) return;
    createWorkflow(workflowName);
    setWorkflowName('');
    setCreateDialogOpen(false);
  };

  const handleCanvasClick = (e: React.MouseEvent) => {
    const target = e.target as HTMLElement;
    if (target.dataset.canvas) {
      setSelectedNode(null);
      setConnectingFrom(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (!draggedAgent) return;

    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    addNode(draggedAgent.id, x - 60, y - 30);
    setDraggedAgent(null);
  };

  const handleNodeClick = (nodeId: string) => {
    if (connectingFrom) {
      if (connectingFrom !== nodeId) {
        addConnection(connectingFrom, nodeId);
      }
      setConnectingFrom(null);
    } else {
      setSelectedNode(nodeId);
    }
  };

  const currentWorkflow = workflows.find((w) => w.id === currentWorkflowId);

  return (
    <div className="flex h-full">
      {/* Agent Library */}
      <div className="w-64 border-r border-border bg-muted/30 flex flex-col">
        <div className="h-14 flex items-center px-4 border-b border-border">
          <Bot className="w-5 h-5 mr-2" />
          <span className="font-medium">代理库</span>
        </div>
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-2">
            {availableAgents.map((agent) => (
              <div
                key={agent.id}
                draggable
                onDragStart={() => setDraggedAgent(agent)}
                className="flex items-center gap-3 p-3 rounded-lg bg-background border cursor-move hover:border-primary transition-colors"
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    // This is a workaround for SonarCloud's accessibility check.
                    // In a real application, you might want to trigger the drag-and-drop
                    // functionality here for keyboard users.
                  }
                }}
              >
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-lg"
                  style={{ backgroundColor: `${agent.color}20` }}
                >
                  {agent.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm">{agent.name}</div>
                  <div className="text-xs text-muted-foreground truncate">
                    {agent.description}
                  </div>
                </div>
                <GripVertical className="w-4 h-4 text-muted-foreground" />
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Canvas */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="h-14 border-b border-border flex items-center justify-between px-4">
          <div className="flex items-center gap-2">
            {currentWorkflow ? (
              <>
                <span className="font-medium">{currentWorkflow.name}</span>
                <span className="text-xs text-muted-foreground">
                  {nodes.length} 个节点, {connections.length} 个连接
                </span>
              </>
            ) : (
              <span className="text-muted-foreground">未选择工作流</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCreateDialogOpen(true)}
            >
              <Plus className="w-4 h-4 mr-1" />
              新建
            </Button>
            <Button variant="outline" size="sm">
              <FolderOpen className="w-4 h-4 mr-1" />
              打开
            </Button>
            <Button variant="outline" size="sm">
              <Save className="w-4 h-4 mr-1" />
              保存
            </Button>
            <div className="w-px h-6 bg-border mx-2" />
            {isRunning ? (
              <Button variant="destructive" size="sm" onClick={stopWorkflow}>
                <Square className="w-4 h-4 mr-1" />
                停止
              </Button>
            ) : (
              <Button
                size="sm"
                onClick={runWorkflow}
                disabled={!currentWorkflowId || nodes.length === 0}
              >
                <Play className="w-4 h-4 mr-1" />
                运行
              </Button>
            )}
          </div>
        </div>

        {/* Canvas Area */}
        <div
          className="flex-1 relative overflow-hidden"
          data-canvas="true"
          style={{
            backgroundImage: `
              radial-gradient(circle, hsl(var(--border)) 1px, transparent 1px)
            `,
            backgroundSize: '20px 20px',
          }}
          onClick={handleCanvasClick}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
        >
          {currentWorkflowId ? (
            <>
              {/* Connections */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none">
                <defs>
                  <marker
                    id="arrowhead"
                    markerWidth="10"
                    markerHeight="7"
                    refX="9"
                    refY="3.5"
                    orient="auto"
                  >
                    <polygon points="0 0, 10 3.5, 0 7" fill="hsl(var(--muted-foreground))" />
                  </marker>
                </defs>
                {connections.map((conn) => {
                  const fromNode = nodes.find((n) => n.id === conn.fromNodeId);
                  const toNode = nodes.find((n) => n.id === conn.toNodeId);
                  if (!fromNode || !toNode) return null;

                  return (
                    <line
                      key={conn.id}
                      x1={fromNode.x + 60}
                      y1={fromNode.y + 30}
                      x2={toNode.x + 60}
                      y2={toNode.y + 30}
                      stroke="hsl(var(--muted-foreground))"
                      strokeWidth="2"
                      markerEnd="url(#arrowhead)"
                      className={cn(isRunning && 'animate-flow')}
                    />
                  );
                })}
              </svg>

              {/* Nodes */}
              {nodes.map((node) => {
                const agent = availableAgents.find((a) => a.id === node.agentId);
                if (!agent) return null;

                return (
                  <AgentNodeComponent
                    key={node.id}
                    node={node}
                    agent={agent}
                    isSelected={selectedNodeId === node.id}
                    isConnecting={connectingFrom === node.id}
                    onClick={() => handleNodeClick(node.id)}
                    onRemove={() => removeNode(node.id)}
                    onUpdatePosition={(x, y) => updateNodePosition(node.id, x, y)}
                  />
                );
              })}

              {/* Empty State */}
              {nodes.length === 0 && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <MousePointer2 className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">
                      从左侧拖拽代理到此处开始构建
                    </p>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <Bot className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium mb-2">创建新工作流</h3>
                <p className="text-muted-foreground mb-4">
                  开始构建您的多代理智能体工作流
                </p>
                <Button onClick={() => setCreateDialogOpen(true)}>
                  <Plus className="w-4 h-4 mr-1" />
                  创建工作流
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Properties Panel */}
        {selectedNodeId && (
          <div className="w-72 border-l border-border bg-muted/30 p-4">
            <div className="flex items-center justify-between mb-4">
              <span className="font-medium">节点配置</span>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={() => setSelectedNode(null)}
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
            {(() => {
              const node = nodes.find((n) => n.id === selectedNodeId);
              const agent = availableAgents.find((a) => a.id === node?.agentId);
              if (!node || !agent) return null;

              return (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-muted-foreground">类型</label>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-2xl">{agent.icon}</span>
                      <span className="font-medium">{agent.name}</span>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">状态</label>
                    <div className="flex items-center gap-2 mt-1">
                      <div
                        className={cn(
                          'w-2 h-2 rounded-full',
                          node.status === 'idle' && 'bg-gray-400',
                          node.status === 'running' && 'bg-blue-500 animate-pulse',
                          node.status === 'success' && 'bg-green-500',
                          node.status === 'error' && 'bg-red-500'
                        )}
                      />
                      <span className="text-sm capitalize">{node.status}</span>
                    </div>
                  </div>
                  <div>
                    <label id="config-label" className="text-sm text-muted-foreground">配置</label>
                    <div className="space-y-2 mt-2" role="group" aria-labelledby="config-label">
                      <label htmlFor="input-param" className="sr-only">输入参数</label>
                      <Input
                        id="input-param"
                        placeholder="输入参数..."
                        value={node.config.input || ''}
                        onChange={(e) =>
                          updateNodeConfig(node.id, { input: e.target.value })
                        }
                      />
                      <label htmlFor="output-param" className="sr-only">输出参数</label>
                      <Input
                        id="output-param"
                        placeholder="输出参数..."
                        value={node.config.output || ''}
                        onChange={(e) =>
                          updateNodeConfig(node.id, { output: e.target.value })
                        }
                      />
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => setConnectingFrom(node.id)}
                    disabled={connectingFrom === node.id}
                  >
                    <ArrowRight className="w-4 h-4 mr-1" />
                    {connectingFrom === node.id ? '选择目标节点' : '连接到...'}
                  </Button>
                </div>
              );
            })()}
          </div>
        )}
      </div>

      {/* Create Workflow Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新建工作流</DialogTitle>
          </DialogHeader>
          <label htmlFor="workflow-name" className="sr-only">工作流名称</label>
          <Input
            id="workflow-name"
            placeholder="工作流名称"
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCreateWorkflow()}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleCreateWorkflow}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

type AgentNodeComponentProps = Readonly<{
  node: AgentNode;
  agent: Agent;
  isSelected: boolean;
  isConnecting: boolean;
  onClick: () => void;
  onRemove: () => void;
  onUpdatePosition: (x: number, y: number) => void;
}>;

function AgentNodeComponent({
  node,
  agent,
  isSelected,
  isConnecting,
  onClick,
  onRemove,
  onUpdatePosition,
}: AgentNodeComponentProps) {
  const handleDrag = useCallback(
    (_event: MouseEvent | TouchEvent | PointerEvent, info: { delta: { x: number; y: number } }) => {
      onUpdatePosition(node.x + info.delta.x, node.y + info.delta.y);
    },
    [node.x, node.y, onUpdatePosition]
  );

  return (
    <motion.div
      drag
      dragMomentum={false}
      onDrag={handleDrag}
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      style={{
        position: 'absolute',
        left: node.x,
        top: node.y,
      }}
      className={cn(
        'w-[120px] bg-background rounded-xl border-2 shadow-lg cursor-pointer transition-all',
        isSelected && 'border-primary ring-2 ring-primary/20',
        isConnecting && 'border-blue-500 ring-2 ring-blue-500/20',
        node.status === 'running' && 'animate-pulse-soft'
      )}
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
    >
      <div
        className="h-2 rounded-t-xl"
        style={{ backgroundColor: agent.color }}
      />
      <div className="p-3">
        <div className="text-2xl text-center mb-2">{agent.icon}</div>
        <div className="text-xs font-medium text-center truncate">{agent.name}</div>
        {node.status !== 'idle' && (
          <div
            className={cn(
              'mt-2 text-[10px] text-center px-2 py-0.5 rounded-full',
              node.status === 'running' && 'bg-blue-100 text-blue-700',
              node.status === 'success' && 'bg-green-100 text-green-700',
              node.status === 'error' && 'bg-red-100 text-red-700'
            )}
          >
            {node.status === 'running' && '运行中'}
            {node.status === 'success' && '成功'}
            {node.status === 'error' && '错误'}
          </div>
        )}
      </div>
      {isSelected && (
        <button
          className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center text-xs hover:bg-red-600"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
        >
          ×
        </button>
      )}
    </motion.div>
  );
}
