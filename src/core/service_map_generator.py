"""
Service Map Generator - Visualize Dependencies
===============================================

Generate interactive service dependency maps
"""

import networkx as nx
from typing import Dict, List, Optional, Tuple
import json


class ServiceMapGenerator:
    """
    Generate service dependency maps
    
    Features:
    - Build dependency graph
    - Detect critical paths
    - Identify single points of failure
    - Calculate service criticality
    - Export to visualization formats (Mermaid, D3.js, Cytoscape)
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.graph = nx.DiGraph()
    
    async def build_service_map(self, team_id: str) -> nx.DiGraph:
        """
        Build complete service dependency graph
        
        Args:
            team_id: Team identifier
        
        Returns:
            NetworkX directed graph
        """
        # Get all services
        services = await self.supabase.table('services').select(
            'id, name, role, criticality'
        ).eq('team_id', team_id).execute()
        
        # Get all dependencies
        dependencies = await self.supabase.table('service_dependencies').select(
            'service_id, depends_on_service_id, dependency_type'
        ).execute()
        
        # Build graph
        self.graph.clear()
        
        # Add nodes (services)
        for service in services.data:
            self.graph.add_node(
                service['id'],
                name=service['name'],
                role=service.get('role', 'application'),
                criticality=service.get('criticality', 0.5)
            )
        
        # Add edges (dependencies)
        for dep in dependencies.data:
            self.graph.add_edge(
                dep['service_id'],
                dep['depends_on_service_id'],
                type=dep.get('dependency_type', 'calls')
            )
        
        return self.graph
    
    def find_critical_services(self) -> List[Dict]:
        """
        Identify critical services (high centrality, many dependents)
        
        Returns:
            List of critical services with scores
        """
        if not self.graph.nodes():
            return []
        
        # Calculate betweenness centrality
        # (services that are on many dependency paths)
        centrality = nx.betweenness_centrality(self.graph)
        
        # Calculate in-degree (how many services depend on this)
        in_degree = dict(self.graph.in_degree())
        
        # Combine metrics
        critical_services = []
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            score = (
                centrality.get(node_id, 0) * 0.4 +
                (in_degree.get(node_id, 0) / max(in_degree.values(), default=1)) * 0.3 +
                node_data.get('criticality', 0.5) * 0.3
            )
            
            critical_services.append({
                'service_id': node_id,
                'name': node_data.get('name'),
                'criticality_score': round(score, 3),
                'centrality': round(centrality.get(node_id, 0), 3),
                'dependents_count': in_degree.get(node_id, 0)
            })
        
        # Sort by criticality
        critical_services.sort(key=lambda x: x['criticality_score'], reverse=True)
        
        return critical_services
    
    def find_single_points_of_failure(self) -> List[Dict]:
        """
        Find services that, if removed, would disconnect the graph
        
        Returns:
            List of SPOFs
        """
        if not self.graph.nodes():
            return []
        
        # Convert to undirected for connectivity analysis
        undirected = self.graph.to_undirected()
        
        # Find articulation points (cut vertices)
        articulation_points = list(nx.articulation_points(undirected))
        
        spofs = []
        for node_id in articulation_points:
            node_data = self.graph.nodes[node_id]
            dependents = list(self.graph.predecessors(node_id))
            
            spofs.append({
                'service_id': node_id,
                'name': node_data.get('name'),
                'role': node_data.get('role'),
                'dependents': len(dependents),
                'warning': 'Single point of failure - consider redundancy'
            })
        
        return spofs
    
    def calculate_blast_radius_visual(self, service_id: str) -> Dict:
        """
        Calculate visual blast radius (what breaks if this service fails)
        
        Args:
            service_id: Service to analyze
        
        Returns:
            Affected services grouped by distance
        """
        if service_id not in self.graph.nodes():
            return {'error': 'Service not found in graph'}
        
        # Find all services that depend on this (directly or indirectly)
        affected = nx.ancestors(self.graph, service_id)
        
        # Group by distance (hops)
        affected_by_distance = {}
        for affected_id in affected:
            try:
                distance = nx.shortest_path_length(self.graph, affected_id, service_id)
                if distance not in affected_by_distance:
                    affected_by_distance[distance] = []
                
                affected_by_distance[distance].append({
                    'service_id': affected_id,
                    'name': self.graph.nodes[affected_id].get('name')
                })
            except nx.NetworkXNoPath:
                continue
        
        return {
            'source_service': service_id,
            'total_affected': len(affected),
            'affected_by_distance': affected_by_distance
        }
    
    def export_to_mermaid(self) -> str:
        """
        Export graph to Mermaid diagram syntax
        
        Returns:
            Mermaid markdown string
        """
        lines = ['graph TD']
        
        # Add nodes with styling
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            name = node_data.get('name', node_id)
            role = node_data.get('role', 'application')
            
            # Style based on role
            if role == 'database':
                style = f'{node_id}[({name})]'
            elif role == 'api':
                style = f'{node_id}[{name}]'
            elif role == 'frontend':
                style = f'{node_id}>{name}]'
            else:
                style = f'{node_id}[{name}]'
            
            lines.append(f'    {style}')
        
        # Add edges
        for source, target in self.graph.edges():
            edge_data = self.graph.edges[source, target]
            dep_type = edge_data.get('type', 'calls')
            lines.append(f'    {source} -->|{dep_type}| {target}')
        
        # Add styling
        lines.append('')
        lines.append('    classDef database fill:#f9f,stroke:#333,stroke-width:2px')
        lines.append('    classDef api fill:#bbf,stroke:#333,stroke-width:2px')
        lines.append('    classDef frontend fill:#bfb,stroke:#333,stroke-width:2px')
        
        return '\n'.join(lines)
    
    def export_to_cytoscape(self) -> Dict:
        """
        Export graph to Cytoscape.js format
        
        Returns:
            JSON-compatible dict for Cytoscape
        """
        elements = []
        
        # Add nodes
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            elements.append({
                'data': {
                    'id': node_id,
                    'label': node_data.get('name', node_id),
                    'role': node_data.get('role', 'application'),
                    'criticality': node_data.get('criticality', 0.5)
                },
                'classes': node_data.get('role', 'application')
            })
        
        # Add edges
        for source, target in self.graph.edges():
            edge_data = self.graph.edges[source, target]
            elements.append({
                'data': {
                    'id': f'{source}-{target}',
                    'source': source,
                    'target': target,
                    'type': edge_data.get('type', 'calls')
                }
            })
        
        return {
            'elements': elements,
            'style': [
                {
                    'selector': 'node',
                    'style': {
                        'label': 'data(label)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'background-color': '#38bdf8',
                        'color': '#fff',
                        'font-size': '12px',
                        'width': '60px',
                        'height': '60px'
                    }
                },
                {
                    'selector': 'node.database',
                    'style': {
                        'shape': 'cylinder',
                        'background-color': '#818cf8'
                    }
                },
                {
                    'selector': 'edge',
                    'style': {
                        'width': 2,
                        'line-color': '#71717a',
                        'target-arrow-color': '#71717a',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        'label': 'data(type)',
                        'font-size': '10px',
                        'text-rotation': 'autorotate'
                    }
                }
            ],
            'layout': {
                'name': 'dagre',
                'rankDir': 'TB',
                'nodeSep': 80,
                'rankSep': 100
            }
        }
    
    def export_to_d3(self) -> Dict:
        """
        Export graph to D3.js force-directed format
        
        Returns:
            JSON-compatible dict for D3
        """
        nodes = []
        links = []
        
        # Create node index map
        node_index = {node_id: idx for idx, node_id in enumerate(self.graph.nodes())}
        
        # Add nodes
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            nodes.append({
                'id': node_id,
                'name': node_data.get('name', node_id),
                'role': node_data.get('role', 'application'),
                'criticality': node_data.get('criticality', 0.5)
            })
        
        # Add links
        for source, target in self.graph.edges():
            edge_data = self.graph.edges[source, target]
            links.append({
                'source': node_index[source],
                'target': node_index[target],
                'type': edge_data.get('type', 'calls')
            })
        
        return {
            'nodes': nodes,
            'links': links
        }
    
    def get_dependency_chain(self, service_id: str) -> List[List[str]]:
        """
        Get all dependency chains for a service
        
        Returns:
            List of dependency paths (chains)
        """
        if service_id not in self.graph.nodes():
            return []
        
        # Find all leaf nodes (nodes with no outgoing edges)
        leaf_nodes = [n for n in self.graph.nodes() if self.graph.out_degree(n) == 0]
        
        chains = []
        for leaf in leaf_nodes:
            try:
                paths = list(nx.all_simple_paths(self.graph, service_id, leaf))
                chains.extend(paths)
            except nx.NetworkXNoPath:
                continue
        
        return chains


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_service_map():
        # Mock Supabase
        class MockSupabase:
            def table(self, name):
                return self
            
            def select(self, *args):
                return self
            
            def eq(self, *args):
                return self
            
            async def execute(self):
                class Result:
                    data = [
                        {'id': 'svc-1', 'name': 'Frontend', 'role': 'frontend', 'criticality': 0.7},
                        {'id': 'svc-2', 'name': 'API Gateway', 'role': 'api', 'criticality': 0.9},
                        {'id': 'svc-3', 'name': 'Database', 'role': 'database', 'criticality': 1.0}
                    ]
                return Result()
        
        generator = ServiceMapGenerator(MockSupabase())
        
        # Build map
        graph = await generator.build_service_map('team-1')
        print(f"Service graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        
        # Export to Mermaid
        mermaid = generator.export_to_mermaid()
        print(f"\nMermaid diagram:\n{mermaid}")
    
    asyncio.run(test_service_map())
