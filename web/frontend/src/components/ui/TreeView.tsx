import { useState, useMemo } from 'react';
import { cn } from '@/lib/utils';

interface TreeNode {
  id: string | number;
  label: string;
  children?: TreeNode[];
  meta?: React.ReactNode;
  code?: string;
}

interface TreeViewProps {
  nodes: TreeNode[];
  onSelect?: (node: TreeNode) => void;
  searchable?: boolean;
  searchPlaceholder?: string;
  defaultExpanded?: boolean;
  className?: string;
}

export function TreeView({
  nodes,
  onSelect,
  searchable = false,
  searchPlaceholder = 'بحث في الحسابات...',
  defaultExpanded = true,
  className,
}: TreeViewProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string | number>>(() => {
    if (!defaultExpanded) return new Set();
    const ids = new Set<string | number>();
    const collect = (items: TreeNode[]) => {
      items.forEach((item) => {
        if (item.children && item.children.length > 0) {
          ids.add(item.id);
          collect(item.children);
        }
      });
    };
    collect(nodes);
    return ids;
  });

  const [search, setSearch] = useState('');
  const [selectedId, setSelectedId] = useState<string | number | null>(null);

  const filteredNodes = useMemo(() => {
    if (!search.trim()) return nodes;
    const q = search.toLowerCase();
    const filterTree = (items: TreeNode[]): TreeNode[] => {
      return items
        .map((item) => {
          const matchesSelf =
            item.label.toLowerCase().includes(q) ||
            (item.code && item.code.toLowerCase().includes(q));
          const filteredChildren = item.children ? filterTree(item.children) : [];
          if (matchesSelf || filteredChildren.length > 0) {
            return { ...item, children: filteredChildren.length > 0 ? filteredChildren : item.children };
          }
          return null;
        })
        .filter(Boolean) as TreeNode[];
    };
    return filterTree(nodes);
  }, [nodes, search]);

  const toggleExpand = (id: string | number) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className={cn('card p-0 overflow-hidden', className)}>
      {searchable && (
        <div className="px-4 py-3 border-b border-gray-200 dark:border-zinc-700">
          <div className="relative">
            <svg
              className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 dark:text-zinc-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={searchPlaceholder}
              className="input pr-10 text-sm"
            />
          </div>
        </div>
      )}
      <div className="divide-y divide-gray-100 dark:divide-zinc-800">
        {filteredNodes.map((node) => (
          <TreeNodeItem
            key={node.id}
            node={node}
            level={0}
            expandedIds={expandedIds}
            selectedId={selectedId}
            onToggle={toggleExpand}
            onSelect={(n) => {
              setSelectedId(n.id);
              onSelect?.(n);
            }}
          />
        ))}
        {filteredNodes.length === 0 && (
          <div className="px-4 py-8 text-center text-sm text-gray-500 dark:text-zinc-400">
            لا توجد نتائج
          </div>
        )}
      </div>
    </div>
  );
}

function TreeNodeItem({
  node,
  level,
  expandedIds,
  selectedId,
  onToggle,
  onSelect,
}: {
  node: TreeNode;
  level: number;
  expandedIds: Set<string | number>;
  selectedId: string | number | null;
  onToggle: (id: string | number) => void;
  onSelect: (node: TreeNode) => void;
}) {
  const hasChildren = node.children && node.children.length > 0;
  const isExpanded = expandedIds.has(node.id);
  const isSelected = selectedId === node.id;

  return (
    <div>
      <div
        className={cn(
          'flex items-center gap-2 px-4 py-2 text-sm transition-colors cursor-pointer',
          isSelected
            ? 'bg-primary-50 dark:bg-primary-500/10 text-primary-700 dark:text-primary-400'
            : 'hover:bg-gray-50 dark:hover:bg-zinc-800/50 text-gray-700 dark:text-zinc-300'
        )}
        style={{ paddingRight: `${(level * 24) + 16}px` }}
        onClick={() => {
          if (hasChildren) onToggle(node.id);
          onSelect(node);
        }}
      >
        {hasChildren ? (
          <svg
            className={cn(
              'h-4 w-4 text-gray-400 dark:text-zinc-500 transition-transform duration-200 flex-shrink-0',
              isExpanded && 'rotate-90'
            )}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        ) : (
          <span className="w-4 flex-shrink-0" />
        )}

        {node.code && (
          <span className="font-mono text-xs text-gray-500 dark:text-zinc-400 bg-gray-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded">
            {node.code}
          </span>
        )}

        <span className="flex-1 truncate">{node.label}</span>

        {node.meta && (
          <span className="text-xs text-gray-500 dark:text-zinc-400 ml-2">{node.meta}</span>
        )}
      </div>

      {hasChildren && isExpanded && (
        <div className="animate-slide-down">
          {node.children!.map((child) => (
            <TreeNodeItem
              key={child.id}
              node={child}
              level={level + 1}
              expandedIds={expandedIds}
              selectedId={selectedId}
              onToggle={onToggle}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}
