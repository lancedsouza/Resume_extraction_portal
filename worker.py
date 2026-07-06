import redis
from rq import Worker, Queue, Connection
import processing # Import your logic

conn = redis.Redis(host='redis', port=6379)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker([Queue('resume_tasks', connection=conn)])
        print("Worker is ready and waiting for jobs...")
        worker.work()