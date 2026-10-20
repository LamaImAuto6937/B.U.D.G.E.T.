import os
from app import create_app
from ModuleOperationClasses import Scheduler
import atexit
from waitress import serve


app = create_app()

# .env Variables
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").upper() == "TRUE"
HOST_IP     = os.getenv("HOST_IP", "127.0.0.1")
HOST_PORT   = int(os.getenv("HOST_PORT", 8080))
PROXY_IP    = os.getenv("PROXY_IP")

if __name__ == "__main__":
    
    # Start Background Jobs
    if not FLASK_DEBUG or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        backgroundJobs = Scheduler()
        backgroundJobs.cleanup_unverified_users()
        backgroundJobs.run()

        backgroundJobs.show_job_info()
        # Terminates backgroundJobs on Program Shutdown
        atexit.register(lambda: backgroundJobs.shutdown()) 
        
    if FLASK_DEBUG: 
        app.run(debug=FLASK_DEBUG, 
                host=HOST_IP, 
                port=HOST_PORT)
        
        
    else:
        if PROXY_IP:
            serve(app=app,
                host=HOST_IP, 
                port=HOST_PORT,
                trusted_proxy=PROXY_IP,
                trusted_proxy_count= 1,
                trusted_proxy_headers="x-forwarded-for x-forwarded-proto")
        else:
            serve(app=app,
                host=HOST_IP, 
                port=HOST_PORT )
        
    
    