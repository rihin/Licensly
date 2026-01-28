import uvicorn
import socket

def get_local_ip():
    try:
        # Get local IP address for convenience
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "0.0.0.0"

if __name__ == "__main__":
    local_ip = get_local_ip()
    print("="*50)
    print(f"🚀 Starting License Management App on LAN")
    print(f"🔗 Local Access:   http://127.0.0.1:8000")
    print(f"🌐 Network Access: http://{local_ip}:8000")
    print("="*50)
    
    # Run server on 0.0.0.0 to be accessible via LAN
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
