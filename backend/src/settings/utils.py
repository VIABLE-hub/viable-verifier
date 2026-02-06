import socket
import requests
import logging
import platform
import subprocess
import os
import time
import psutil
import datetime

# Initialize logger for utils module
logger = logging.getLogger(__name__)

def get_local_ip():
    """Get the local IP address of the machine"""
    # Try multiple methods to get a valid IP address
    ip_address = "127.0.0.1"  # Default fallback
    
    # Method 1: Connect to external server
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        if not ip_address.startswith('127.'):
            return ip_address
    except Exception as e:
        logging.debug(f"Method 1 error: {e}")
    
    # Method 2: Get from hostname
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        if not ip_address.startswith('127.'):
            return ip_address
    except Exception as e:
        logging.debug(f"Method 2 error: {e}")
    
    # Method 3: Try all interfaces
    try:
        for ip in socket.getaddrinfo(socket.gethostname(), None):
            if ip[0] == socket.AF_INET and not ip[4][0].startswith('127.'):
                return ip[4][0]
    except Exception as e:
        logging.debug(f"Method 3 error: {e}")
    
    # Method 4: Try to get IP from network interfaces (platform specific)
    try:
        if platform.system() == "Darwin":  # macOS
            # Try to get IP from active network interface
            result = subprocess.run(['ipconfig', 'getifaddr', 'en0'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            # Try en1 if en0 doesn't work
            result = subprocess.run(['ipconfig', 'getifaddr', 'en1'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
    except Exception as e:
        logging.debug(f"Method 4 error: {e}")
        
    # Return whatever we have at this point
    return ip_address

def get_public_ip():
    """Get public IP address using an external service"""
    try:
        response = requests.get('https://api.ipify.org', timeout=5)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        logging.debug(f"Error getting public IP: {e}")
    
    try:
        # Try alternative service
        response = requests.get('https://ifconfig.me/ip', timeout=5)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        logging.debug(f"Error getting public IP (backup method): {e}")
    
    return "unknown"

def get_network_information():
    """Get basic network information"""
    hostname = socket.gethostname()
    local_ip = get_local_ip()
    public_ip = get_public_ip()
    
    return {
        "hostname": hostname,
        "local_ip": local_ip,
        "public_ip": public_ip
    }

def test_http_connection(url, timeout=5):
    """Test HTTP connection to a URL"""
    start_time = time.time()
    try:
        response = requests.get(url, timeout=timeout, verify=False)
        elapsed = time.time() - start_time
        return {
            "status": "success" if response.status_code < 400 else "error",
            "message": f"HTTP {response.status_code}",
            "latency": round(elapsed * 1000, 2)  # Convert to ms
        }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "status": "error",
            "message": str(e),
            "latency": round(elapsed * 1000, 2)  # Convert to ms
        }

def test_socket_connection(host, port, timeout=5):
    """Test socket connection to a host and port"""
    start_time = time.time()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        elapsed = time.time() - start_time
        return {
            "status": "success",
            "message": "Connected",
            "latency": round(elapsed * 1000, 2)  # Convert to ms
        }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "status": "error",
            "message": str(e),
            "latency": round(elapsed * 1000, 2)  # Convert to ms
        }

def format_bytes(size):
    """
    Format bytes to a human-readable format
    """
    if size == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = 0
    while size >= 1024 and i < len(size_name) - 1:
        size /= 1024
        i += 1
    return f"{size:.2f} {size_name[i]}"

def format_time_delta(seconds):
    """
    Format a time delta in seconds to a human-readable format (HH:MM:SS)
    """
    if seconds < 0:
        return "00:00:00"
    
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 24:
        days, hours = divmod(hours, 24)
        return f"{int(days)}d {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    else:
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

def get_system_uptime():
    """Get system uptime in seconds"""
    try:
        if platform.system() == "Windows":
            return time.time() - psutil.boot_time()
        else:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
            return uptime_seconds
    except:
        # Fallback to psutil for all platforms
        try:
            return time.time() - psutil.boot_time()
        except:
            return 0

def format_uptime(seconds):
    """Format uptime in seconds to human-readable string"""
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days > 0:
        return f"{int(days)}d {int(hours)}h {int(minutes)}m"
    elif hours > 0:
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    elif minutes > 0:
        return f"{int(minutes)}m {int(seconds)}s"
    else:
        return f"{int(seconds)}s"

def format_datetime(dt):
    """Format datetime to human-readable string"""
    if not dt:
        return "n/a"
    
    if isinstance(dt, str):
        try:
            dt = datetime.datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            try:
                dt = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
            except:
                return dt  # Return original if parsing fails
    
    # Format with timezone if available
    if dt.tzinfo:
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_hostname():
    """Get system hostname"""
    try:
        return socket.gethostname()
    except:
        return "unknown" 