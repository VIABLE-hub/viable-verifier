from flask import Blueprint, jsonify
import os
import psutil
import time
import platform
import datetime

monitoring = Blueprint('monitoring', __name__, url_prefix='/api/monitoring')

def get_size(bytes, suffix="B"):
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

@monitoring.route('/system')
def system_info():
    """System-Informationen für das Monitoring Dashboard"""
    try:
        # System-Informationen
        uname = platform.uname()
        
        # Boot-Zeit
        boot_time_timestamp = psutil.boot_time()
        bt = datetime.datetime.fromtimestamp(boot_time_timestamp)
        
        # CPU-Informationen
        cpufreq = psutil.cpu_freq()
        
        # RAM-Informationen
        svmem = psutil.virtual_memory()
        
        # Festplatten-Informationen
        disk_usage = psutil.disk_usage('/')
        
        # Netzwerk-Informationen
        net_io = psutil.net_io_counters()
        
        # Prozesse
        process_count = len(list(psutil.process_iter()))
        
        return jsonify({
            "system": {
                "system": uname.system,
                "node_name": uname.node,
                "release": uname.release,
                "version": uname.version,
                "machine": uname.machine,
                "processor": uname.processor
            },
            "cpu": {
                "physical_cores": psutil.cpu_count(logical=False),
                "total_cores": psutil.cpu_count(logical=True),
                "max_frequency": f"{cpufreq.max:.2f}Mhz" if cpufreq else "N/A",
                "current_frequency": f"{cpufreq.current:.2f}Mhz" if cpufreq else "N/A",
                "usage_per_core": [round(percentage, 2) for percentage in psutil.cpu_percent(interval=0.1, percpu=True)],
                "total_usage": round(psutil.cpu_percent(interval=0.1), 2)
            },
            "memory": {
                "total": get_size(svmem.total),
                "available": get_size(svmem.available),
                "used": get_size(svmem.used),
                "percentage": svmem.percent,
            },
            "disk": {
                "total": get_size(disk_usage.total),
                "used": get_size(disk_usage.used),
                "free": get_size(disk_usage.free),
                "percentage": disk_usage.percent
            },
            "network": {
                "bytes_sent": get_size(net_io.bytes_sent),
                "bytes_received": get_size(net_io.bytes_recv),
                "packets_sent": net_io.packets_sent,
                "packets_received": net_io.packets_recv
            },
            "boot_time": {
                "timestamp": boot_time_timestamp,
                "formatted": bt.strftime("%Y-%m-%d %H:%M:%S"),
                "uptime": str(datetime.datetime.now() - bt).split('.')[0]  # Uptime ohne Millisekunden
            },
            "processes": {
                "count": process_count
            },
            "timestamp": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Fehler beim Abrufen der Systeminfos"
        }), 500

@monitoring.route('/database')
def database_info():
    """Datenbank-Informationen für das Monitoring Dashboard"""
    try:
        # Diese Funktion würde normalerweise echte Datenbankstatistiken abfragen
        # Hier als Beispiel statische Daten
        return jsonify({
            "connection_pool": {
                "active_connections": 12,
                "idle_connections": 3,
                "max_connections": 100
            },
            "performance": {
                "queries_per_second": 42.7,
                "avg_query_time": 0.0053,
                "slow_queries": 2
            },
            "storage": {
                "total_size": "4.2 GB",
                "index_size": "1.1 GB",
                "table_count": 15
            },
            "operations": {
                "inserts": 2345,
                "updates": 1203,
                "deletes": 421,
                "selects": 45678
            },
            "timestamp": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Fehler beim Abrufen der Datenbankstatistiken"
        }), 500

@monitoring.route('/credentials')
def credentials_info():
    """Credential-Statistiken für das Monitoring Dashboard"""
    try:
        # Diese Funktion würde normalerweise echte Credential-Statistiken abfragen
        # Hier als Beispiel statische Daten
        return jsonify({
            "issuance": {
                "total": 5432,
                "last_24h": 87,
                "last_7d": 542,
                "by_type": {
                    "StudentIDCard": 3254,
                    "UniversityDegree": 1203,
                    "CourseCredential": 975
                }
            },
            "verification": {
                "total": 8765,
                "successful": 8234,
                "failed": 531,
                "last_24h": 145
            },
            "revocation": {
                "total": 123,
                "active": 8642,
                "last_7d": 12
            },
            "timestamp": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Fehler beim Abrufen der Credential-Statistiken"
        }), 500
