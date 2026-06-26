import os
from app import create_app
from ModuleOperationClasses import Scheduler
import atexit

app = create_app()

if __name__ == "__main__":
    
    # Start Background Jobs
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        backgroundJobs = Scheduler()
        backgroundJobs.cleanup_unverified_users()
        backgroundJobs.run()

        backgroundJobs.show_job_info()
        # Terminates backgroundJobs on Program Shutdown
        atexit.register(lambda: backgroundJobs.shutdown()) 
    
    app.run(debug=True, host=str(os.getenv("HOST_IP")), port=int(os.getenv("HOST_PORT")))


