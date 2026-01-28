"""
Dependency Analyzer - Service Dependency Graph
==============================================

Builds and analyzes service dependency graph for:
- Cascade failure prediction
- Blast radius calculation  
- Critical path identification
- Impact analysis

Uses NetworkX for graph operations.
"""

from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict
import json

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    print("Warning: networkx not installed. Run: pip install networkx")


class DependencyType:
    """Dependency relationship types"""
    HARD = "hard"        # Service cannot function without dependency
    SOFT = "soft"        # Service degraded without dependency
    OPTIONAL = "optional"  # Service works fine without dependency


class DependencyAnalyzer:
    """
    Analyzes service dependency graphs to understand failure impact
    
    Graph Structure:
        - Nodes: Services
        - Edges: Dependencies (directional: parent → child)
        - Edge attributes: dependency_type (hard/soft/optional)
    
    Use Cases:
        1. Calculate blast radius when service fails
        2. Predict cascade failures
        3. Identify critical services (single points of failure)
        4. Generate service map visualization
    """
    
    def __init__(self, db_client=None):
        """
        Initialize dependency analyzer
        
        Args:
            db_client: Database client for fetching service dependencies
        """
        self.db = db_client
        self.graph = nx.DiGraph() if NETWORKX_AVAILABLE else None
        self._initialized = False
    
    async def build_graph(self):
        """
        Build dependency graph from database
        
        Fetches:
        - All services (nodes)
        - All dependencies (edges)
        """
        if not self.graph:
            print("NetworkX not available - dependency analysis disabled")
            return
        
        # Clear existing graph
        self.graph.clear()
        
        # Fetch services from database
        services = await self._fetch_services()
        
        # Add nodes
        for svc in services:
            self.graph.add_node(
                svc['id'],
                name=svc['name'],
                criticality=svc.get('criticality_score', 0.5),
                role=svc.get('role', 'standard')
            )
        
        # Fetch dependencies
        dependencies = await self._fetch_dependencies()
        
        # Add edges
        for dep in dependencies:
            self.graph.add_edge(
                dep['parent_service_id'],
                dep['child_service_id'],
                dependency_type=dep.get('dependency_type', DependencyType.HARD)
            )
        
        self._initialized = True
        print(f"Built dependency graph: {len(self.graph.nodes)} services, {len(self.graph.edges)} dependencies")
    
    def calculate_blast_radius(self, service_id: str) -> Dict:
        """
        Calculate how many downstream services are affected if this service fails
        
        Args:
            service_id: Service UUID that failed
        
        Returns:
            Dict with:
            - affected_services: List of service IDs
            - blast_radius: Count of affected services
            - critical_path: Whether on critical path
            - severity_multiplier: Impact multiplier
        """
        if not self.graph or service_id not in self.graph:
            return {
                'affected_services': [],
                'blast_radius': 0,
                'critical_path': False,
                'severity_multiplier': 1.0
            }
        
        # Find all descendants (services that depend on this one, directly or indirectly)
        try:
            descendants = nx.descendants(self.graph, service_id)
        except nx.NetworkXError:
            descendants = set()
        
        # Filter for hard dependencies only (soft deps can handle gracefully)
        critical_descendants = self._get_hard_dependents(service_id, descendants)
        
        # Check if on critical path (any descendant has only this service as dependency)
        is_critical_path = self._is_on_critical_path(service_id, descendants)
        
        # Calculate severity multiplier based on impact
        criticality = self.graph.nodes[service_id].get('criticality', 0.5)
        blast_size = len(critical_descendants)
        
        # Multiplier: 1.0 (no impact) to 3.0 (massive impact)
        severity_multiplier = 1.0 + (blast_size * 0.2) + (criticality * 0.5)
        severity_multiplier = min(severity_multiplier, 3.0)
        
        return {
            'affected_services': list(critical_descendants),
            'blast_radius': len(critical_descendants),
            'critical_path': is_critical_path,
            'severity_multiplier': severity_multiplier
        }
    
    def get_cascade_prediction(self, failed_service_id: str) -> List[Dict]:
        """
        Predict which services will fail next (cascade failures)
        
        Args:
            failed_service_id: Service that just failed
        
        Returns:
            List of services likely to fail next, sorted by risk
        """
        if not self.graph or failed_service_id not in self.graph:
            return []
        
        # Get immediate successors (services that call this one)
        try:
            immediate_dependents = list(self.graph.successors(failed_service_id))
        except nx.NetworkXError:
            immediate_dependents = []
        
        cascade_risks = []
        
        for svc_id in immediate_dependents:
            edge_data = self.graph.get_edge_data(failed_service_id, svc_id)
            dep_type = edge_data.get('dependency_type', DependencyType.HARD)
            
            # Calculate risk score
            if dep_type == DependencyType.HARD:
                risk_score = 0.9  # 90% chance of failure
            elif dep_type == DependencyType.SOFT:
                risk_score = 0.5  # 50% chance of degradation
            else:
                risk_score = 0.1  # 10% chance of impact
            
            # Get service details
            svc_data = self.graph.nodes[svc_id]
            
            cascade_risks.append({
                'service_id': svc_id,
                'service_name': svc_data.get('name', 'Unknown'),
                'dependency_type': dep_type,
                'risk_score': risk_score,
                'criticality': svc_data.get('criticality', 0.5)
            })
        
        # Sort by risk score (highest first)
        cascade_risks.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return cascade_risks
    
    def identify_single_points_of_failure(self) -> List[Dict]:
        """
        Find services that are single points of failure (SPOFs)
        
        A service is a SPOF if:
        - Multiple services depend on it (high out-degree)
        - Removing it disconnects the graph
        
        Returns:
            List of SPOF services with impact analysis
        """
        if not self.graph:
            return []
        
        spofs = []
        
        for node in self.graph.nodes():
            # Count dependents
            out_degree = self.graph.out_degree(node)
            
            if out_degree >= 3:  # Has 3+ dependents
                blast_radius = self.calculate_blast_radius(node)
                
                spofs.append({
                    'service_id': node,
                    'service_name': self.graph.nodes[node].get('name'),
                    'dependent_count': out_degree,
                    'blast_radius': blast_radius['blast_radius'],
                    'criticality': self.graph.nodes[node].get('criticality', 0.5)
                })
        
        # Sort by impact (blast radius * criticality)
        spofs.sort(
            key=lambda x: x['blast_radius'] * x['criticality'],
            reverse=True
        )
        
        return spofs
    
    def get_service_health_score(self, service_id: str) -> float:
        """
        Calculate health score based on dependency health
        
        If dependencies are unhealthy, this service may be impacted
        
        Args:
            service_id: Service to check
        
        Returns:
            Health score (0.0-1.0)
        """
        if not self.graph or service_id not in self.graph:
            return 1.0
        
        # Get predecessors (services this one depends on)
        try:
            dependencies = list(self.graph.predecessors(service_id))
        except nx.NetworkXError:
            dependencies = []
        
        if not dependencies:
            return 1.0  # No dependencies = healthy
        
        # TODO: Fetch actual health status from database
        # For now, return 1.0 (healthy)
        return 1.0
    
    def visualize_graph(self) -> Dict:
        """
        Generate graph data for frontend visualization (D3.js/React Flow compatible)
        
        Returns:
            Dict with nodes and edges arrays
        """
        if not self.graph:
            return {'nodes': [], 'edges': []}
        
        nodes = []
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            nodes.append({
                'id': node_id,
                'name': node_data.get('name', 'Unknown'),
                'criticality': node_data.get('criticality', 0.5),
                'role': node_data.get('role', 'standard'),
                'dependent_count': self.graph.out_degree(node_id)
            })
        
        edges = []
        for source, target in self.graph.edges():
            edge_data = self.graph.get_edge_data(source, target)
            edges.append({
                'source': source,
                'target': target,
                'type': edge_data.get('dependency_type', DependencyType.HARD)
            })
        
        return {
            'nodes': nodes,
            'edges': edges
        }
    
    def _get_hard_dependents(
        self,
        service_id: str,
        descendants: Set[str]
    ) -> Set[str]:
        """Filter descendants for hard dependencies only"""
        hard_deps = set()
        
        for desc in descendants:
            # Check if path from service_id to desc has any hard dependencies
            try:
                paths = nx.all_simple_paths(self.graph, service_id, desc)
                for path in paths:
                    # Check edges in path
                    has_hard_dep = False
                    for i in range(len(path) - 1):
                        edge_data = self.graph.get_edge_data(path[i], path[i+1])
                        if edge_data.get('dependency_type') == DependencyType.HARD:
                            has_hard_dep = True
                            break
                    
                    if has_hard_dep:
                        hard_deps.add(desc)
                        break
            except nx.NetworkXNoPath:
                pass
        
        return hard_deps
    
    def _is_on_critical_path(
        self,
        service_id: str,
        descendants: Set[str]
    ) -> bool:
        """Check if service is on critical path (descendant has no alternatives)"""
        for desc in descendants:
            # Get predecessors of descendant
            try:
                predecessors = list(self.graph.predecessors(desc))
                if len(predecessors) == 1:
                    # Only one dependency - critical path
                    return True
            except nx.NetworkXError:
                pass
        
        return False
    
    async def _fetch_services(self) -> List[Dict]:
        """Fetch services from database (placeholder)"""
        # TODO: Implement actual DB query
        return []
    
    async def _fetch_dependencies(self) -> List[Dict]:
        """Fetch dependencies from database (placeholder)"""
        # TODO: Implement actual DB query
        return []


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_dependency_analyzer():
        analyzer = DependencyAnalyzer()
        
        # Mock data
        if analyzer.graph:
            # Add test services
            analyzer.graph.add_node('auth', name='Auth API', criticality=1.0)
            analyzer.graph.add_node('api', name='Main API', criticality=0.9)
            analyzer.graph.add_node('db', name='Database', criticality=1.0)
            analyzer.graph.add_node('cache', name='Redis Cache', criticality=0.7)
            
            # Add dependencies
            analyzer.graph.add_edge('auth', 'api', dependency_type='hard')
            analyzer.graph.add_edge('db', 'auth', dependency_type='hard')
            analyzer.graph.add_edge('db', 'api', dependency_type='hard')
            analyzer.graph.add_edge('cache', 'api', dependency_type='soft')
            
            # Test blast radius
            blast = analyzer.calculate_blast_radius('db')
            print(f"Database failure blast radius: {blast}")
            
            # Test cascade prediction
            cascade = analyzer.get_cascade_prediction('auth')
            print(f"Cascade prediction if Auth fails: {cascade}")
    
    asyncio.run(test_dependency_analyzer())
