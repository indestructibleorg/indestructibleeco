# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: python-module
# @ECO-audit-trail: ../../engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
#
# GL Unified Architecture Governance Framework Activated
# GL Root Semantic Anchor: gl-enterprise-architecture/governance/engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
# GL Unified Naming Charter: gl-enterprise-architecture/governance/engine/governance/gl-artifacts/meta/naming-charter/gl-unified-naming-charter.yaml

"""
Semantic Engine REST API Server
Provides HTTP endpoints for semantic engine operations
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
# MNGA-002: Import organization needs review
from flask import Flask, request, jsonify
from typing import Dict, Any
import yaml
import os

from .gl-platform.gl-platform.governance.semantic_engine import SemanticEngine
import traceback


app = Flask(__name__)
engine = SemanticEngine(embedding_dim=128)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'GL Semantic Core Engine',
        'version': '1.0.0'
    })


@app.route('/semantic/load', methods=['POST'])
def load_specification():
    """Load semantic specification from YAML"""
    try:
        data = request.get_json()
        spec_yaml = data.get('specification')
        
        if not spec_yaml:
            return jsonify({'error': 'No specification provided'}), 400
        
        graph = engine.load_specification(spec_yaml)
        
        return jsonify({
            'success': True,
            'message': 'Specification loaded successfully',
            'stats': engine.get_stats()
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/semantic/query', methods=['GET'])
def query_semantic():
    """Query semantic node by ID"""
    try:
        node_id = request.args.get('id')
        
        if not node_id:
            return jsonify({'error': 'Node ID required'}), 400
        
        result = engine.query(node_id)
        
        if result is None:
            return jsonify({'error': 'Node not found'}), 404
        
        return jsonify({
            'success': True,
            'node': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/semantic/search', methods=['GET'])
def semantic_search():
    """Semantic search"""
    try:
        query = request.args.get('query', '')
        top_k = int(request.args.get('top_k', 10))
        threshold = float(request.args.get('threshold', 0.0))
        
        results = engine.semantic_search(query, top_k=top_k, threshold=threshold)
        
        # Convert to JSON-serializable format
        json_results = []
        for node_id, score in results:
            node = engine.indexing.query_by_id(node_id)
            if node:
                json_results.append({
                    'id': node.id,
                    'type': node.type.value,
                    'score': float(score),
                    'features': node.features,
                    'metadata': node.metadata
                })
        
        return jsonify({
            'success': True,
            'query': query,
            'results': json_results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/semantic/feature/<feature>', methods=['GET'])
def query_by_feature(feature):
    """Query nodes by feature"""
    try:
        results = engine.query_by_feature(feature)
        
        return jsonify({
            'success': True,
            'feature': feature,
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/semantic/infer/capabilities/<domain_id>', methods=['GET'])
def infer_capabilities(domain_id):
    """Infer capabilities for a domain"""
    try:
        capabilities = engine.infer_capabilities(domain_id)
        
        return jsonify({
            'success': True,
            'domain': domain_id,
            'capabilities': capabilities
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/semantic/infer/resources/<capability_id>', methods=['GET'])
def infer_resources(capability_id):
    """Infer resources for a capability"""
    try:
        resources = engine.infer_resources(capability_id)
        
        return jsonify({
            'success': True,
            'capability': capability_id,
            'resources': resources
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/semantic/validate/conflict', methods=['POST'])
def validate_conflict():
    """Validate conflict between two nodes"""
    try:
        data = request.get_json()
        node_a_id = data.get('node_a_id')
        node_b_id = data.get('node_b_id')
        
        if not node_a_id or not node_b_id:
            return jsonify({'error': 'Both node_a_id and node_b_id required'}), 400
        
        result = engine.validate_conflict(node_a_id, node_b_id)
        
        return jsonify({
            'success': True,
            'validation': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/semantic/validate/completeness/<node_id>', methods=['GET'])
def validate_completeness(node_id):
    """Validate completeness of a node"""
    try:
        result = engine.validate_completeness(node_id)
        
        return jsonify({
            'success': True,
            'validation': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/semantic/map/ui/<internal_id>', methods=['GET'])
def map_to_ui(internal_id):
    """Map internal ID to UI representation"""
    try:
        result = engine.map_internal_to_ui(internal_id)
        
        if result is None:
            return jsonify({'error': 'Node not found'}), 404
        
        return jsonify({
            'success': True,
            'mapping': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/semantic/stats', methods=['GET'])
def get_stats():
    """Get engine statistics"""
    try:
        stats = engine.get_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/semantic/export', methods=['GET'])
def export_graph():
    """Export semantic graph"""
    try:
        graph = engine.export_graph()
        
        return jsonify({
            'success': True,
            'graph': graph
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting GL Semantic Core Engine API Server...")
    print("API Documentation: http://localhost:5000/")
    print("Health Check: http://localhost:5000/health")
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host='0.0.0.0', port=5000, debug=debug)