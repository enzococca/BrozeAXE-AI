"""
System Blueprint
================

Endpoints for system health, status, and monitoring.
"""

from flask import Blueprint, jsonify
import os
import sys
from datetime import datetime
from acs.core.database import ArtifactDatabase
from acs.core.auth import login_required

# Optional psutil for system monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

system_bp = Blueprint('system', __name__)

# Global database instance
db = ArtifactDatabase()


@system_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Public endpoint (no authentication required).

    Returns:
        JSON with system health status:
        - status: 'healthy' or 'unhealthy'
        - timestamp: Current timestamp
        - version: Application version
        - uptime: Server uptime (if available)
        - checks: Individual health checks
    """
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '0.1.0',
        'checks': {}
    }

    # Check database connectivity
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.fetchone()
        health_status['checks']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'message': f'Database error: {str(e)}'
        }

    # Check disk space
    if PSUTIL_AVAILABLE:
        try:
            disk_usage = psutil.disk_usage('/')
            disk_percent = disk_usage.percent

            if disk_percent > 90:
                health_status['status'] = 'unhealthy'
                status = 'critical'
            elif disk_percent > 80:
                status = 'warning'
            else:
                status = 'healthy'

            health_status['checks']['disk_space'] = {
                'status': status,
                'usage_percent': disk_percent,
                'free_gb': round(disk_usage.free / (1024**3), 2),
                'total_gb': round(disk_usage.total / (1024**3), 2)
            }
        except Exception as e:
            health_status['checks']['disk_space'] = {
                'status': 'unknown',
                'message': f'Could not check disk space: {str(e)}'
            }
    else:
        health_status['checks']['disk_space'] = {
            'status': 'unavailable',
            'message': 'psutil not installed'
        }

    # Check memory
    if PSUTIL_AVAILABLE:
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            if memory_percent > 90:
                status = 'warning'
            else:
                status = 'healthy'

            health_status['checks']['memory'] = {
                'status': status,
                'usage_percent': memory_percent,
                'available_gb': round(memory.available / (1024**3), 2),
                'total_gb': round(memory.total / (1024**3), 2)
            }
        except Exception as e:
            health_status['checks']['memory'] = {
                'status': 'unknown',
                'message': f'Could not check memory: {str(e)}'
            }
    else:
        health_status['checks']['memory'] = {
            'status': 'unavailable',
            'message': 'psutil not installed'
        }

    # Return appropriate status code
    status_code = 200 if health_status['status'] == 'healthy' else 503

    return jsonify(health_status), status_code


@system_bp.route('/status', methods=['GET'])
@login_required
def system_status():
    """
    Detailed system status endpoint.

    Requires: authentication

    Returns:
        JSON with detailed system information:
        - System resources (CPU, memory, disk)
        - Database statistics
        - Python version
        - Loaded modules count
    """
    try:
        # System information
        status = {
            'timestamp': datetime.now().isoformat(),
            'version': '0.1.0',
            'system': {}
        }

        # Python info
        status['system']['python_version'] = sys.version
        status['system']['platform'] = sys.platform

        # CPU info
        if PSUTIL_AVAILABLE:
            try:
                status['system']['cpu'] = {
                    'count': psutil.cpu_count(),
                    'usage_percent': psutil.cpu_percent(interval=1),
                    'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
                }
            except:
                status['system']['cpu'] = {'status': 'unavailable'}
        else:
            status['system']['cpu'] = {'status': 'psutil not installed'}

        # Memory info
        if PSUTIL_AVAILABLE:
            try:
                memory = psutil.virtual_memory()
                status['system']['memory'] = {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2),
                    'usage_percent': memory.percent
                }
            except:
                status['system']['memory'] = {'status': 'unavailable'}
        else:
            status['system']['memory'] = {'status': 'psutil not installed'}

        # Disk info
        if PSUTIL_AVAILABLE:
            try:
                disk = psutil.disk_usage('/')
                status['system']['disk'] = {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'used_gb': round(disk.used / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'usage_percent': disk.percent
                }
            except:
                status['system']['disk'] = {'status': 'unavailable'}
        else:
            status['system']['disk'] = {'status': 'psutil not installed'}

        # Database statistics
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Count artifacts
                cursor.execute('SELECT COUNT(*) as count FROM artifacts')
                artifacts_count = cursor.fetchone()['count']

                # Count classifications
                cursor.execute('SELECT COUNT(*) as count FROM classifications')
                classifications_count = cursor.fetchone()['count']

                # Count training samples
                cursor.execute('SELECT COUNT(*) as count FROM training_data')
                training_count = cursor.fetchone()['count']

                # Count users
                cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_active = 1')
                users_count = cursor.fetchone()['count']

                # Database file size
                db_path = db.db_path
                db_size_mb = round(os.path.getsize(db_path) / (1024**2), 2) if os.path.exists(db_path) else 0

                status['database'] = {
                    'path': db_path,
                    'size_mb': db_size_mb,
                    'artifacts': artifacts_count,
                    'classifications': classifications_count,
                    'training_samples': training_count,
                    'active_users': users_count
                }
        except Exception as e:
            status['database'] = {
                'status': 'error',
                'message': str(e)
            }

        return jsonify({
            'status': 'success',
            **status
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@system_bp.route('/info', methods=['GET'])
def system_info():
    """
    Basic system information endpoint (public).

    Returns:
        JSON with basic system information:
        - Application name and version
        - API endpoints count
        - Authentication status
    """
    return jsonify({
        'name': 'BrozeAXE-AI Archaeological Classifier',
        'version': '0.1.0',
        'description': 'Archaeological artifact classification and analysis system',
        'api_version': 'v1',
        'documentation': '/api/docs',
        'health_check': '/api/system/health',
        'authentication': 'JWT-based authentication required for most endpoints',
        'features': [
            '3D mesh processing',
            'Savignano axe analysis',
            'Morphometric analysis',
            'PCA and clustering',
            'AI-powered classification',
            'Comprehensive PDF reports'
        ]
    })


@system_bp.route('/backup', methods=['POST'])
@login_required
def backup_database():
    """
    Trigger manual database backup to configured storage.

    Requires: authentication (admin recommended)

    Returns:
        JSON with backup status:
        - status: 'success' or 'error'
        - backup_path: Path to backup in storage
        - timestamp: Backup timestamp
        - storage_backend: Storage backend used
    """
    try:
        from acs.core.database import backup_database_to_storage

        result = backup_database_to_storage()

        if result['status'] == 'success':
            return jsonify(result), 200
        elif result['status'] == 'disabled':
            return jsonify(result), 200
        else:
            return jsonify(result), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500
